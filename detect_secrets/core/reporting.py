# TODO: convert to object literal / type, if possible
# TODO: annotate types
# TODO: make JSON serializable
# Reference: https://github.com/Yelp/detect-secrets/
# blob/2f4f956e4fa3610efeeeb989b3ef11df9a171011/detect_secrets/util/code_snippet.py#L36
class ReportedSecret:
    failed_condition: str
    filename: str
    line: int
    type: str  # reserved word? if so use category

    def __init__(self, failed_condition, filename, line, type):
        self.failed_condition = failed_condition
        self.filename = filename
        self.line = line
        self.type = type
        pass
