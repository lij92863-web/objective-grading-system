# SRE561 Review Architecture

Responsibility: retain unresolved recognition/identity findings, teacher resolution and append-only audit evidence. Inputs are ErrorCode-based ReviewItems; outputs are queue/summary and audited resolution state. Review depends on errors/common time only. It cannot grade, mutate original evidence or resolve identity blocking through answer review.

Unresolved items block confirmation. Overrides require notes, and resolution records actor/time without replacing evidence. Future persistence may serialize the same model. Risks are shallow external mutation and authorization, which remain outside this non-web stage.
