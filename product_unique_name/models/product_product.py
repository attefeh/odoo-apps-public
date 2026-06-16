from odoo import _, api, models
from odoo.exceptions import ValidationError


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _unique_name_key(self):
        """Return the full variant name used to detect duplicates: the product
        name plus its attribute values, e.g. ``T-Shirt (Red, L)``. Two variants
        of the same template differ by their attribute values, so this stays
        unique for legitimate variants while still catching real duplicates."""
        self.ensure_one()
        name = (self.name or "").strip()
        attributes = self.product_template_attribute_value_ids.mapped("name")
        if attributes:
            name = "%s (%s)" % (name, ", ".join(attributes))
        return name

    @api.constrains("name", "product_template_attribute_value_ids", "company_id")
    def _check_unique_variant_name(self):
        """Forbid two variants sharing the same full name (name + attributes).

        Matching is case-insensitive and whitespace-trimmed. As with products,
        a name may be reused across companies but not within one company or
        against a shared (no-company) variant."""
        for variant in self:
            if not (variant.name or "").strip():
                continue

            # Variants share their template's name, so narrow the candidates by
            # that bare name first, then compare the full attribute-aware name.
            domain = [
                ("id", "!=", variant.id),
                ("name", "=ilike", (variant.name or "").strip()),
            ]
            if variant.company_id:
                domain.append(
                    ("company_id", "in", (False, variant.company_id.id))
                )

            target = variant._unique_name_key().casefold()
            duplicate = self.sudo().search(domain).filtered(
                lambda v: v._unique_name_key().casefold() == target
            )[:1]
            if duplicate:
                raise ValidationError(_(
                    "A product variant named \"%(name)s\" already exists "
                    "(%(ref)s). Variant names must be unique.",
                    name=variant._unique_name_key(),
                    ref=duplicate.display_name,
                ))
