"""JSON for single-decision model replies, not saved results or tool plans."""
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
