from odoo import _, api, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.constrains("name", "company_id")
    def _check_unique_product_name(self):
        """Forbid two products sharing the same name.

        The match is case-insensitive and ignores leading/trailing spaces, so
        "Desk", "desk" and " Desk " all count as the same name. In a
        multi-company database a name may still be reused across companies: a
        company-specific product only clashes with another product of the same
        company or with a shared (no-company) product."""
        for template in self:
            name = (template.name or "").strip()
            if not name:
                continue

            domain = [
                ("id", "!=", template.id),
                # =ilike is a (case-insensitive) pattern match; the exact,
                # whitespace-trimmed comparison below is the real check.
                ("name", "=ilike", name),
            ]
            if template.company_id:
                domain.append(
                    ("company_id", "in", (False, template.company_id.id))
                )

            target = name.casefold()
            duplicate = self.sudo().search(domain).filtered(
                lambda p: (p.name or "").strip().casefold() == target
            )[:1]
            if duplicate:
                raise ValidationError(_(
                    "A product named \"%(name)s\" already exists (%(ref)s). "
                    "Product names must be unique.",
                    name=template.name,
                    ref=duplicate.display_name,
                ))
