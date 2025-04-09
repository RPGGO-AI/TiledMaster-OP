from tiled_master.utils.utils import write_json
import json


class Rule:
    def __init__(self, pattern: str, local_id: int):
        """
        :param pattern: A string of length 8, allowing characters '1', '0', '*', e.g. "1*******"
        :param local_id: The local_id corresponding to this rule
        """
        self.pattern = pattern[::-1]
        self.local_id = local_id

    def matches(self, config):
        """
        Determines if the given adjacency configuration matches the rule
        :param config: A string of length 8, containing only '1' and '0' (e.g. "10101010")
        :return: True if it matches; otherwise False
        """
        for i in range(8):
            # If the rule character is not '*', the position must match the configuration
            if self.pattern[i] != '*' and self.pattern[i] != config[i]:
                return False
        return True


def load_rules_from_json(filename):
    """
    Load rule configurations from JSON file
    :param filename: JSON file path
    :return: List of Rule objects
    """
    with open(filename, 'r', encoding='utf-8') as f:
        config = json.load(f)

    rules = []
    for rule_conf in config.get("rules", []):
        pattern = rule_conf.get("pattern")
        local_id = rule_conf.get("local_id")
        if not pattern or len(pattern) != 8:
            raise ValueError(f"Invalid rule pattern: {pattern}, must be 8 characters.")
        rules.append(Rule(pattern, local_id))
    return rules


def generate_mapping(rules):
    """
    Traverse all 256 adjacency states (0~255) to generate mapping.
    Each state is matched against rules by converting to an 8-bit binary string.
    The mapping key is the corresponding decimal number, and the value is the matching local_id (None if no match).

    :param rules: List of Rule objects
    :return: dict, keys are integers (0~255), values are matching local_id (None if no match)
    """
    mapping = {}
    for num in range(256):
        # Convert number to 8-bit binary string (e.g., 5 -> "00000101")
        config = format(num, '08b')
        matched_local_id = None
        # Apply rules in order, the first matching rule takes effect
        for rule in rules:
            if rule.matches(config):
                matched_local_id = rule.local_id
                break
        mapping[num] = matched_local_id
    return mapping


def inner_16():
    # Specify JSON configuration file path
    config_file = "./blob47_config.json"
    rules = load_rules_from_json(config_file)
    # Generate adjacency state mapping, keys are decimal numbers
    mapping = generate_mapping(rules)

    # Output mapping (keys are decimal numbers)
    print("Generated adjacency relationship mapping (keys are decimal):")
    for key in sorted(mapping.keys()):
        print(f"{key}: {mapping[key]}")

    write_json("./blob47.json", mapping)

if __name__ == "__main__":
    inner_16()
