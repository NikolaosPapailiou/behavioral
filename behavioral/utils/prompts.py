import string


class PartialPromptParams(dict):
    def __missing__(self, key):
        if key.startswith("eval_"):
            key = key.replace("eval_", "")
            return "{" + self.get(key) + "}"
        return "{" + key + "}"

    def format_with_eval(
        self, prompt: str, string_formatter: string.Formatter = None
    ) -> str:
        if string_formatter is None:
            string_formatter = string.Formatter()
        # format 2 times to handle eval_ keys
        if "eval_" in prompt:
            return self.format(self.format(prompt, string_formatter), string_formatter)
        return self.format(prompt, string_formatter)

    def format(self, prompt: str, string_formatter: string.Formatter = None) -> str:
        if string_formatter is None:
            string_formatter = string.Formatter()
        return str(string_formatter.vformat(prompt, (), self))
