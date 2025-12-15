from .section import SectionExtractor


class EducationExtractor(SectionExtractor):
    def extract(self):
        return self.extract_section(["Education"])
