"""JSON for single-decision model replies, not saved results or tool plans.

Contributed by jwalith4418-Mj in pull request 40 (issue 24): a reply that repeats a decision key is read as
unclear, so each reader falls back to its own fail-closed result rather than silently taking the last value, which
could turn a denial into an approval.
"""
import json


def loads_unique(text: str):
    """The harness's reading: any repeated object key makes a decision unclear.

    Reject nested duplicates too, so a call argument or alarm verdict cannot
    silently replace an earlier value. Readers use their existing parse-failure
    result, including their well-formed flag where one exists.
    """
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise json.JSONDecodeError(f"duplicate reply key: {key}", text, 0)
            result[key] = value
        return result

    return json.loads(text, object_pairs_hook=unique)
