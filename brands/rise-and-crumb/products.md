# Rise & Crumb products

The source of truth for Rise & Crumb product facts. Emails may only state what's written here. If something you need isn't here, ask; don't guess.

> **Status:** sample brand profile written 2026-11-14 to test multi-brand support. Products, prices, pickup times and the address are fictional placeholders, not a real business.

## Weekend bake

All three are baked fresh for **weekend pickup only**. Pre-order online by **Thursday at 6 pm** for that weekend.

| Product | Price | Size | Ingredients | Pickup days |
|---|---|---|---|---|
| **Country Sourdough** | $12 | 900 g loaf | Unbleached wheat flour, whole wheat flour, water, sea salt, sourdough starter | Saturday and Sunday |
| **Seeded Rye** | $14 | 800 g loaf | Rye flour, unbleached wheat flour, water, sunflower seeds, flax seeds, pumpkin seeds, caraway, sea salt, sourdough starter | Saturday only |
| **Cardamom Morning Bun** | $5 each | 1 bun | Sourdough-leavened laminated dough (wheat flour, butter, milk, sugar, sea salt), brown sugar, ground cardamom, orange zest | Saturday and Sunday |

### Bake details

| Product | What it's like | How it's made |
|---|---|---|
| Country Sourdough | Crackly, deep-baked crust; open, chewy crumb; gentle tang | 36-hour ferment, hand-shaped, stone-baked |
| Seeded Rye | Dense, moist crumb; nutty and earthy, with caraway | Proofed overnight, baked in a tin |
| Cardamom Morning Bun | Flaky, buttery layers; warm cardamom and orange | Laminated by hand, rolled with spiced sugar |

## Pickup

| Field | Detail |
|---|---|
| Where | The bakery counter (address below) |
| Hours | Saturday and Sunday, 8 am–1 pm |
| Pre-order cutoff | Thursday, 6 pm |
| Link (draft) | `https://example.com/preorder` |

## Allergens

- All three contain **wheat (gluten)**.
- Cardamom Morning Bun contains **milk**.
- Seeded Rye contains **seeds** (sunflower, flax, pumpkin).
- Everything is baked in a kitchen that handles wheat, milk, eggs, seeds and tree nuts.

## Email footer

Read by `scripts/brand_profile.py` (and so by `check_draft.py` and the guard hooks). Copy these exactly.

| Field | Detail |
|---|---|
| Brand name | Rise & Crumb |
| Mailing address | `Rise & Crumb Bakery, 88 Hearth Street, Unit 3, Asheville, NC 28801, USA` |
| Reason line | `You're getting this because you signed up for Rise & Crumb bake emails.` |
| Contact email | `hello@example.com` |
| Address status | Sample address: replace before sending |

## Things we don't claim

- No health, diet, "clean eating" or gluten-free claims. Sourdough is not gluten-free.
- No "organic" unless an ingredient is listed here as certified (none are).
- No discounts, free items or delivery unless they're added here with dates. We offer pickup only.
- No batch limits or "almost gone" lines unless a limit is listed here.
