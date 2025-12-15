from .section import SectionExtractor


class ExperienceExtractor(SectionExtractor):
    def extract(self):
        return self.extract_section(["Experience", "Work Experience"])
