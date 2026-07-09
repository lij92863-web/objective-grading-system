"""R156: Teacher action registry."""
ACTIONS = ["accept_candidate","correct_answer","mark_blank","reject_candidate",
           "block_submission","confirm_identity","correct_identity","block_identity"]

ACTION_POLICY = {
    "choice": {"allow": ["correct_answer","reject_candidate","block_submission","mark_blank","accept_candidate"],
               "review": ["correct_answer","reject_candidate","block_submission"]},
    "blank": {"allow": ["accept_candidate","correct_answer","mark_blank","block_submission"],
              "review": ["correct_answer","mark_blank","block_submission"]},
    "identity": {"allow": ["confirm_identity","correct_identity","block_identity"],
                 "review": ["confirm_identity","correct_identity","block_identity"]},
    "engine_error": {"allow": ["correct_answer","block_submission"],
                     "review": ["correct_answer","block_submission"]},
    "layout": {"allow": ["block_submission"],
               "review": ["block_submission"]},
    "roi": {"allow": ["correct_answer","mark_blank","block_submission"],
            "review": ["correct_answer","mark_blank","block_submission"]},
}


def allowed_actions(item_type: str, is_blocking: bool = False) -> list:
    p = ACTION_POLICY.get(item_type, ACTION_POLICY["choice"])
    return p["review"] if is_blocking else p["allow"]
