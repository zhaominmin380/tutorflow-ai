\# Tova — Visual Design Specification

Extracted from the approved reference screens (\`TutorFlow Reference v2.dc.html\`: Dashboard / Students / Lesson Record, plus sheet, dialog and state variants).

This documents the design **\*\*as implemented\*\***. No new decisions were added. Where a behaviour is not implemented in the reference, it is marked *\*(not implemented)\** rather than invented.

Target stack: React + Tailwind. All values below are literal from the reference; token names are semantic and stack-agnostic.

\---

\## 1. Design tokens

\### 1.1 Color

Every color used in the reference, mapped to a semantic name. Source palette: \`text #080612\`, \`background #dcd2c4\`, \`primary #a55757\`, \`secondary #d895aa\`, \`accent #c5918c\`.

**\*\*Surfaces\*\***

\| Token | Hex | Use |

\|---|---|---|

\| \`surface-app\` | \`#dcd2c4\` | Page/app background (html, body, root flex container) |

\| \`surface-nav\` | \`#e8ddd0\` | Sidebar background |

\| \`surface-card\` | \`#f7f2ea\` | All cards, tables, sheets, dialogs, search input, secondary toolbar buttons |

\| \`surface-raised\` | \`#ffffff\` | Textareas, secondary buttons that sit *\*on\** a card |

\| \`surface-sunken\` | \`#f2ece2\` | Dashed "not started" placeholder block |

\| \`surface-table-head\` | \`#ebe1d2\` | Table header row |

\| \`surface-row-hover\` | \`#fdf9f3\` | Table row hover |

\| \`surface-highlight\` | \`#f4e6e6\` | "Next lesson" agenda row |

\| \`surface-nav-active\` | \`#eee4d9\` | Active primary-nav item |

\| \`surface-skeleton\` | \`#e2d8c8\` | Loading skeleton bars |

**\*\*Borders / dividers\*\***

\| Token | Hex | Use |

\|---|---|---|

\| \`border-default\` | \`#c9bda9\` | Card, sheet, table outer borders; textarea borders |

\| \`border-strong\` | \`#c2b5a0\` | Interactive borders: buttons, inputs, dashed placeholder |

\| \`border-subtle\` | \`#ded3c2\` | Row dividers inside cards/tables; sheet spec-list gaps |

\| \`border-nav\` | \`#efe7db\` | Sidebar footer divider |

**\*\*Text\*\***

\| Token | Hex | Use |

\|---|---|---|

\| \`text-primary\` | \`#080612\` | Headings, body, input text |

\| \`text-secondary\` | \`#332c40\` | Sheet body copy, tertiary agenda time, table date cells |

\| \`text-tertiary\` | \`#5f5670\` | Descriptive paragraphs, table secondary cells |

\| \`text-muted\` | \`#6d6478\` | Labels, meta lines, captions, inactive nav |

\| \`text-faint\` | \`#847b90\` | Status micro-copy, disabled/absent values ("—", 未安排) |

\| \`text-annotation\` | \`#7a7186\` | Reference-mode annotation text only |

\| \`text-wordmark\` | \`#7a4a34\` | Sidebar wordmark |

\| \`text-brand-sub\` | \`#9c7c68\` | Wordmark sub-label |

\| \`text-on-primary\` | \`#ffffff\` | Text on \`brand-primary\` |

\| \`text-on-nav-active\` | \`#4a2626\` | Active nav label; avatar initial |

\| \`text-on-button-secondary\` | \`#2b2438\` | Secondary/ghost button labels |

**\*\*Brand & accents\*\***

\| Token | Hex | Use |

\|---|---|---|

\| \`brand-primary\` | \`#a55757\` | Primary buttons, links, step badges, mono "NEXT" label, active chip fill |

\| \`brand-primary-hover\` | \`#8a4747\` | Primary button hover |

\| \`brand-primary-soft\` | \`#eddede\` | Scheduled-status chip, filter chips, step-3 badge |

\| \`brand-secondary\` | \`#d895aa\` | Empty-state icon tile, unsaved-draft chip, logo glyph |

\| \`brand-accent\` | \`#c5918c\` | Next-row inset rule, avatar tile, focus ring |

\| \`neutral-button-hover\` | \`#e9e0d2\` | Secondary button hover |

**\*\*Status\*\***

\| Token | Fill | Text | Use |

\|---|---|---|---|

\| \`status-neutral\` | \`#e4dccd\` | \`#7a5a5a\` | 已完成 / 在學 chips, saved chip |

\| \`status-inactive\` | \`#e6ddcf\` | \`#6d6478\` | 已封存 chip |

\| \`status-active\` | \`#eddede\` | \`#a55757\` | 已排定 chip |

\| \`status-draft\` | \`#d895aa\` | \`#4a1f2c\` | 草稿未儲存 chip |

\| \`status-error-surface\` | \`#f6e5e5\` | — | AI error panel background, error chip fill |

\| \`status-error-border\` | \`#dcb9b9\` | — | AI error panel border |

\| \`status-error-text\` | \`#8a3b3b\` | — | Error title / error chip text |

\| \`status-error-body\` | \`#6f4a4a\` | — | Error body copy |

**\*\*Scrims\*\***

\| Token | Value |

\|---|---|

\| \`scrim-sheet\` | \`rgba(8,6,18,0.30)\` |

\| \`scrim-dialog\` | \`rgba(8,6,18,0.38)\` |

\### 1.2 Typography

Families (Google Fonts, weights 400/500/700 and mono 400/500):

\- \`font-sans\`: \`'Noto Sans TC', system-ui, sans-serif\` — all UI text.

\- \`font-mono\`: \`'IBM Plex Mono', monospace\` — **\*\*only\*\*** for time, dates, phone numbers, numerals in stat cards, step-badge digits, and system status micro-copy (autosave, AI status).

\- \`font-display\`: \`'Sacramento', cursive\` — **\*\*only\*\*** the sidebar wordmark. Never for UI text.

Rendering: \`-webkit-font-smoothing: antialiased\` on the root.

\| Role | Size | Weight | Family | Extra |

\|---|---|---|---|---|

\| Wordmark "Tova" | 44px | 400 | display | \`line-height: 1\`, \`#7a4a34\` |

\| Wordmark sub-label | 11.5px | 400 | sans | \`letter-spacing: 0.18em\`, \`text-brand-sub\` |

\| Page title (h1) | 26px | 700 | sans | \`letter-spacing: -0.01em\` |

\| Record page title (h1) | 24px | 700 | sans | \`letter-spacing: -0.01em\` |

\| Sheet title (h2) | 19px | 700 | sans | — |

\| Empty-state title (h2) | 18px / 17px | 700 | sans | 18 on dashboard, 17 on students |

\| Dialog title (h3) | 17px | 700 | sans | — |

\| Section title (h2) | 15px | 700 | sans | — |

\| Stat value | 24px | 700 | mono | unit suffix: 13px / 400 / sans / \`text-muted\` |

\| Body / list primary | 15px | 500 | sans | agenda student name |

\| Body default | 14px | 400–500 | sans | table cells, buttons, inputs |

\| Body compact | 13.5px | 400 | sans | paragraphs (\`line-height:1.7\`), sheet rows, small buttons |

\| Meta | 13px | 400 | sans/mono | links in sheet, mono table dates |

\| Caption | 12.5px | 400 | sans | secondary agenda line, hint text, filter chips |

\| Label / column head | 12px | 400 | sans | field labels, table head, chips |

\| Eyebrow (mono) | 12px | 400 | mono | \`letter-spacing: 0.08em\`, \`text-muted\` |

\| Status micro-copy | 11.5px | 400–500 | mono | autosave state, AI state, chips |

\| Sidebar sub-label | 11px | 400 | sans | 個人教學工作區 |

\| NEXT marker | 10.5px | 400 | mono | \`letter-spacing: 0.06em\`, \`brand-primary\` |

Line-heights in use: \`1.4\` (sidebar identity), \`1.7\` (descriptive paragraphs, summary fields), \`1.75\` (raw-notes textarea, dialog copy), \`1.8\` (feedback textarea, sheet note). \`text-wrap: pretty\` on long-form paragraphs.

Locale rules: Traditional Chinese UI; dates \`YYYY/MM/DD（週）\` or \`MM/DD\`; times 24-hour with en dash (\`14:00–15:00\`); interpunct \`·\` as the meta separator.

\### 1.3 Spacing

4px base. Values actually used: \`1, 2, 3, 4, 5, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 40, 56, 72\`.

Recurring rhythm:

\- Page section stack: \`gap: 22px\` (Dashboard, Lesson Record), \`gap: 20px\` (Students).

\- Card internal stack: \`gap: 14px\`; card padding \`20px 22px\`.

\- Stat/filter card padding: \`16px 18px\`; grid gap \`14px\`.

\- Row padding: agenda \`18px 20px\`, table body \`15px 20px\`, table head \`12px 20px\`.

\- Button/label clusters: \`gap: 10px\` or \`12px\`; chip rows \`gap: 8px\`.

\- Sheet padding \`26px 26px 32px\`, internal stack \`gap: 20px\`.

\- Dialog padding \`24px\`, stack \`gap: 12px\`, action row \`margin-top: 8px\`, \`gap: 10px\`.

\- Empty state padding \`56px 40px\`, stack \`gap: 12–14px\`.

\### 1.4 Radii

\| Token | Value | Use |

\|---|---|---|

\| \`radius-pill\` | \`99px\` | Chips, avatars, step badges, nav dots |

\| \`radius-lg\` | \`16px\` | Cards, tables, sheets… dialogs |

\| \`radius-md\` | \`14px\` | Stat cards, filter card, empty-state icon tile |

\| \`radius-sm\` | \`12px\` | Textareas (large), dashed placeholder, error panel, sheet spec list |

\| \`radius-control\` | \`10px\` | All buttons, inputs, compact textareas |

\| \`radius-skeleton\` | \`6px\` | Skeleton bars |

\### 1.5 Shadows & elevation

Only three elevation treatments exist:

\| Token | Value | Use |

\|---|---|---|

\| \`shadow-sheet\` | \`-24px 0 60px rgba(8,6,18,0.16)\` | Right-edge student detail sheet |

\| \`shadow-dialog\` | \`0 30px 70px rgba(8,6,18,0.26)\` | Archive + draft-exit dialogs |

\| \`inset-highlight\` | \`inset 3px 0 0 #c5918c\` | Left rule on the "next lesson" agenda row |

Cards use **\*\*borders, not shadows\*\***. There is no hover elevation anywhere.

\---

\## 2. Layout

\### 2.1 App shell

Root: \`display\:flex; min-height:100vh; background\:surface-app; color\:text-primary\`.

**\*\*Sidebar\*\*** — \`width:236px; flex:0 0 236px; height:100vh; position\:sticky; top:0; padding:22px 16px; border-right:1px solid border-default; background\:surface-nav; display\:flex; flex-direction\:column; gap:28px\`.

Order: brand block → \`\<nav>\` → user block pushed down with \`margin-top\:auto\`, \`border-top:1px solid border-nav\`, \`padding-top:14px\`.

\- Brand: centered column, \`padding: 8px 6px 0\`, \`gap: 6px\`.

  - Wordmark row: \`display\:flex; align-items\:flex-start; gap:5px; line-height:1\` — the script wordmark "Tova" (44px, \`text-wordmark\`) followed by the leaf mark image (\`assets/leaf.png\`, \`width:26px; height\:auto; margin-top:6px\`, transparent background, no recolouring).

  - Sub-label 「個人教學工作區」: 11.5px, \`letter-spacing:0.18em\`, \`text-brand-sub\`.

  - The wordmark is an **\*\*image + web-font lockup, not an icon tile\*\*** — do not substitute a lettermark badge.

\- User: 28px pill avatar \`brand-accent\` fill / \`text-on-nav-active\` initial, 12px/700; name 12px/500; role 12px \`text-muted\`.

**\*\*Main\*\*** — \`flex:1; min-width:0; max-width:1180px; padding:30px 40px 72px\`.

\### 2.2 Content widths

\- Dashboard & Students: full main width (max 1180px).

\- Lesson Record section: \`max-width:760px\`.

\- Stat card grid: \`max-width:520px\`, \`grid-template-columns: repeat(2, minmax(0,1fr))\`.

\- Search input: \`flex:1; max-width:340px\`.

\- Empty-state paragraph: \`max-width:380px\` (dashboard) / \`340px\` (students).

\- Student sheet: \`width:400px; max-width:92vw\`.

\- Dialogs: \`420px\` (archive) / \`440px\` (draft exit), \`max-width:100%\`.

\### 2.3 Grids

\- Agenda row: \`grid-template-columns: 132px 1fr auto auto; gap:18px; align-items\:center\`.

\- Student table (head and body share the template): \`grid-template-columns: 1.2fr 0.7fr 0.9fr 1.1fr 0.7fr; gap:16px\`.

\---

\## 3. Components

\### 3.1 Primary nav item

\`display\:flex; align-items\:center; gap:10px; padding:10px 12px; border\:none; border-radius:10px; font-size:14px; font-weight:500; text-align\:left; cursor\:pointer\`.

Leading dot: 6×6 pill, \`background: currentColor; opacity:0.55\` — it inherits the label color, so it dims with the inactive state automatically.

\| State | Background | Text |

\|---|---|---|

\| Inactive | \`transparent\` | \`text-tertiary\` |

\| Active | \`surface-nav-active\` (\`#eee4d9\`) | \`text-on-nav-active\` |

No separate hover style is implemented.

\### 3.2 Buttons

\| Variant | Fill | Text | Border | Padding | Size | Hover |

\|---|---|---|---|---|---|---|

\| Primary (page header) | \`brand-primary\` | white | none | \`11px 18px\` | 14/500 | \`brand-primary-hover\` |

\| Primary (in-card) | \`brand-primary\` | white | none | \`10px 18px\` | 14/500 | \`brand-primary-hover\` |

\| Primary (row / dialog) | \`brand-primary\` | white | none | \`9px 16px\` / \`10px 18px\` | 13.5/500 | \`brand-primary-hover\` |

\| Secondary on card | \`surface-raised\` | \`text-on-button-secondary\` | \`1px border-strong\` | \`9px 15px\`–\`11px 16px\` | 13.5–14/500 | \`neutral-button-hover\` |

\| Secondary on page bg | \`surface-card\` | \`text-on-button-secondary\` | \`1px border-strong\` | \`10px 15px\` / \`9px 20px\` | 13.5/500 | \`neutral-button-hover\` |

\| Text/ghost | none | \`brand-primary\` | none | \`10px 12px\` (dialog) / \`0\` (back link, 13px) | 13–13.5/500 | none |

All buttons: \`border-radius: 10px; cursor: pointer\`. Empty-state CTA adds \`margin-top:6px\`, padding \`11px 20px\`.

\### 3.3 Card

\`background: surface-card; border:1px solid border-default; border-radius:16px\` (14px for stat/filter cards). Content stacks use flex column with \`gap:14px\`. List cards use \`overflow\:hidden\` so child row dividers meet the rounded edge; the last row omits its \`border-bottom\`.

\### 3.4 Chip / badge

\`border-radius:99px; font-size:12px; font-weight:500; padding:5px 11px\` (table cells use \`4px 10px\`; record header uses \`6px 12px\`; filter chips 12.5px \`6px 12px\`; AI status chip 11.5px/500 \`5px 11px\`). Fill/text pairs come from the Status token table. Chips are non-interactive except the filter chips, which use \`brand-primary\`/white for the selected value and \`brand-primary-soft\`/\`brand-primary\` for unselected.

\### 3.5 Step badge (Lesson Record)

22×22 pill, mono 12px, centered. Steps 1–2 (required): \`brand-primary\` fill, white text. Step 3 (optional): \`brand-primary-soft\` fill, \`brand-primary\` text. The optional marker "（選填）" follows the heading at 13px/400 \`text-faint\`.

\### 3.6 Inputs

\- Search input: \`background\:surface-card; border:1px solid border-strong; border-radius:10px; padding:10px 14px; font-size:14px; color\:text-primary\`.

\- Textareas: \`background\:surface-raised; border:1px solid border-default; border-radius:12px; padding:14px; resize\:vertical; width:100%\`. Raw notes \`min-height:120px\`, 14px/1.75. Parent feedback \`min-height:150px\`, 13.5px/1.8. Summary fields \`min-height:56px\`, \`border-radius:10px\`, \`padding:11px 13px\`, 13.5px/1.7, each preceded by a 12px \`text-muted\` label with \`gap:6px\`.

\- Focus (global): \`outline: 2px solid brand-accent; outline-offset: 1px\` on \`input\` and \`textarea\`. Buttons have no custom focus ring — keep the UA default or reuse this ring.

\### 3.7 Agenda row

Three visual variants of the same grid:

1\. **\*\*Completed\*\*** — time in \`text-muted\`; student name \`text-muted\` with \`text-decoration: line-through; text-decoration-color: border-strong\`; neutral chip; secondary action.

2\. **\*\*Next (current focus)\*\*** — \`background: surface-highlight\`, \`box-shadow: inset 3px 0 0 brand-accent\`; time 14px/500 \`text-primary\` with a mono \`NEXT\` marker underneath (\`gap:4px\`); active chip; **\*\*primary\*\*** action. Only one row per screen carries a primary action.

3\. **\*\*Upcoming\*\*** — time \`text-secondary\`; active chip; secondary action.

Secondary line under the name: 12.5px, \`text-faint\` when completed, \`text-muted\` otherwise, \`gap:3px\`.

\### 3.8 Student table

Header row: \`surface-table-head\`, \`border-bottom:1px solid border-default\`, 12px \`text-muted\`. Body rows: \`cursor\:pointer\`, \`border-bottom:1px solid border-subtle\` (last row none), hover \`surface-row-hover\`. Name 14px/500; grade & subject \`text-tertiary\`; next-lesson mono 13px \`text-secondary\`, or \`text-faint\` when absent. Archived rows dim every cell to \`text-muted\` / \`text-faint\`. "載入更多" is a centered secondary button below the card (\`gap:14px\`).

\### 3.9 Student detail sheet

Fixed overlay \`inset:0\`, \`scrim-sheet\`, \`z-index:40\`, panel right-aligned; the scrim area left of the panel is a click-to-close target. Panel: \`surface-card\`, \`border-left:1px solid border-default\`, \`shadow-sheet\`, stack \`gap:20px\`.

Spec list: flex column with \`gap:1px\` over a \`border-subtle\` background and a \`1px border-default\` outer border, \`radius-sm\`, \`overflow\:hidden\` — the 1px gaps read as hairline dividers. Each row: \`justify-content\:space-between; padding:12px 14px; background\:surface-card; font-size:13.5px\`, label \`text-muted\`, mono values 13px.

Note paragraph 13.5px/1.8 \`text-secondary\`. Footer pinned with \`margin-top\:auto\`: link (13.5px) then two \`flex:1\` buttons (primary 編輯 / secondary 封存) with \`gap:10px\`. Close "×" is 18px \`text-muted\`, \`padding:2px 4px\`, no border.

\### 3.10 Dialogs

Fixed overlay \`inset:0\`, \`scrim-dialog\`, centered, \`z-index:60\`, \`padding:24px\`. Panel: \`surface-card\`, \`radius-lg\`, \`padding:24px\`, \`shadow-dialog\`, \`gap:12px\`. Title 17px/700; body 13.5px/1.75 \`text-tertiary\`. Actions right-aligned, \`gap:10px\`, \`margin-top:8px\`; destructive-ish confirmation still uses the standard primary fill (no red variant exists). Draft-exit dialog uses three actions in order: ghost 繼續編輯 → secondary 捨棄 → primary 儲存草稿, with \`flex-wrap: wrap\`.

\### 3.11 Empty state

Centered card: \`padding:56px 40px\`, \`align-items\:center; text-align\:center\`. Optional 52×52 \`radius-md\` tile in \`brand-secondary\` with a 20px/700 \`brand-primary\` glyph. Title → paragraph (\`max-width\` per §2.2, 14px/1.7 \`text-tertiary\`) → primary CTA.

\### 3.12 Loading skeleton

Three stacked bars, \`height:12px; radius 6px; background\:surface-skeleton\`, widths \`88% / 74% / 56%\`, \`gap:10px\`, followed by mono 11.5px \`text-faint\` status text. No shimmer animation.

\### 3.13 Error panel

\`border:1px solid status-error-border; background\:status-error-surface; radius:12px; padding:16px 18px; gap:10px\`. Title 14px/500 \`status-error-text\`; body 13.5px/1.7 \`status-error-body\`; actions \`gap:10px\` — primary retry plus a secondary manual-fallback button, so the task is never blocked.

\---

\## 4. Interaction states

\| Element | States implemented |

\|---|---|

\| Nav item | inactive / active (background + text swap) |

\| Primary button | default / hover (\`brand-primary-hover\`) |

\| Secondary button | default / hover (\`neutral-button-hover\`) |

\| Table row | default / hover (\`surface-row-hover\`) / click → opens sheet |

\| Input, textarea | default / focus ring (\`brand-accent\`, offset 1) |

\| Filter panel | collapsed / expanded (toggled by the 篩選 button) |

\| Raw notes | not started (dashed placeholder + CTA) / started (textarea) |

\| Autosave status (mono, top-right of card) | \`尚未建立紀錄\` → \`自動儲存已啟用\` → \`儲存中…\` → \`已自動儲存 HH\:MM\` (settles \~800ms after the last keystroke) |

\| AI summary | idle / loading (skeleton, \~1.1s) / error / draft / manual / saved |

\| AI status chip | idle \`—\` transparent+\`text-faint\` · loading \`brand-primary-soft\` · error \`status-error-\*\` · draft & manual \`status-draft\` · saved \`status-neutral\` |

\| Summary hint text | unsaved \`儲存後才會成為課堂紀錄的一部分\` / saved \`已存入這堂課的紀錄\` |

\| Parent feedback | locked (before summary save) / ready / draft / copied (\`已複製到剪貼簿\`, \`#7a5a5a\`) |

\| Draft exit | dialog when leaving with an unsaved draft; save / discard / keep editing |

\| Archive | confirmation dialog from the sheet |

Editing any summary field re-enters the \`draft\` state and clears \`saved\`. There are no CSS transitions or animations anywhere in the reference — state changes are instantaneous.

Disabled styling is **\*\*not\*\*** used: unavailable steps (parent feedback before the summary is saved) hide their controls and show an explanatory 13.5px \`text-faint\` line instead.

\---

\## 5. Responsive behaviour

As implemented, the reference is a **\*\*fixed desktop layout\*\***: no media queries, no breakpoint changes. Reproduce these facts rather than inventing breakpoints:

\- Sidebar is always 236px, sticky, full viewport height.

\- Main is fluid between the sidebar and a 1180px max width, with 40px side padding.

\- Only three fluid rules exist: the sheet's \`max-width:92vw\`, dialogs' \`max-width:100%\` inside 24px overlay padding, and the stat grid's \`minmax(0,1fr)\` columns.

\- Agenda rows and table rows are fixed-template grids and will not reflow below roughly 900px of main width.

\- The product spec calls for bottom navigation and a full-screen scheduling sheet on mobile — *\*not implemented in these screens\**; treat as a separate design task.

\- Theme is **\*\*light only\*\***. No dark mode; do not add \`dark:\` variants.

\---

\## 6. Component-level rules (do not break)

1\. **\*\*One primary action per screen region.\*\*** Page headers carry one primary button; in the agenda only the next lesson gets the filled button — every other row is secondary.

2\. **\*\*Cards are bordered, never shadowed.\*\*** Shadow is reserved for overlay layers (sheet, dialog).

3\. **\*\*Mono font is data-only\*\***: times, dates, numerals, phone numbers, and system status. Never for prose, labels, or buttons.

4\. **\*\*Chips never carry actions\*\***; they report status only (the filter panel's selectable chips are the single exception).

5\. **\*\*Save state is always visible\*\*** next to the section title, in mono at 11.5px, right-aligned.

6\. **\*\*AI output is always editable and never blocking\*\***: every AI state offers a manual path (自行撰寫 / 重試).

7\. **\*\*Destructive-adjacent actions are two-step\*\*** (封存 → confirmation dialog). There is no delete affordance and no red button variant.

8\. **\*\*Status chips reuse the token pairs in §1.1\*\*** — do not introduce new status colors; the palette has no green or blue.

9\. **\*\*Warm neutrals dominate; \`brand-primary\` is used sparingly\*\*** — buttons, links, badges, and one chip. Large tinted areas use \`surface-highlight\` or \`brand-primary-soft\`, never full-strength primary.

10\. **\*\*Wordmark is fixed\*\***: script face + leaf asset, centered, never inline with a badge or resized below 40px.

11\. **\*\*Rounded scale is intentional\*\***: 99px chips, 16px containers, 10px controls. Do not use a single global radius.

\---

\## 7. Tailwind mapping hint

\`\`\`js

// tailwind.config.js — theme.extend

colors: {

  surface: { app:'#dcd2c4', nav:'#e8ddd0', card:'#f7f2ea', raised:'#ffffff', sunken:'#f2ece2',

             tablehead:'#ebe1d2', rowhover:'#fdf9f3', highlight:'#f4e6e6', navactive:'#eee4d9', skeleton:'#e2d8c8' },

  border:  { DEFAULT:'#c9bda9', strong:'#c2b5a0', subtle:'#ded3c2', nav:'#efe7db' },

  ink:     { DEFAULT:'#080612', secondary:'#332c40', tertiary:'#5f5670', muted:'#6d6478', faint:'#847b90',

             onprimary:'#ffffff', onnav:'#4a2626', onbutton:'#2b2438' },

  brand:   { DEFAULT:'#a55757', hover:'#8a4747', soft:'#eddede', secondary:'#d895aa', accent:'#c5918c' },

  status:  { neutral:'#e4dccd', neutralink:'#7a5a5a', inactive:'#e6ddcf', draft:'#d895aa', draftink:'#4a1f2c',

             errorbg:'#f6e5e5', errorborder:'#dcb9b9', errorink:'#8a3b3b', errorbody:'#6f4a4a' }

},

fontFamily: { sans:["'Noto Sans TC'",'system-ui','sans-serif'], mono:["'IBM Plex Mono'",'monospace'],

              display:["'Sacramento'",'cursive'] },

borderRadius: { control:'10px', sm:'12px', md:'14px', lg:'16px', pill:'99px' },

boxShadow: {

  sheet:'-24px 0 60px rgba(8,6,18,0.16)',

  dialog:'0 30px 70px rgba(8,6,18,0.26)',

  nextrow:'inset 3px 0 0 #c5918c'

}

\`\`\`

Font sizes at 12.5px / 13.5px / 11.5px are intentional and outside Tailwind's default scale — add them as \`text-[13.5px]\` utilities or explicit \`fontSize\` entries; do not round them to 12/14px.