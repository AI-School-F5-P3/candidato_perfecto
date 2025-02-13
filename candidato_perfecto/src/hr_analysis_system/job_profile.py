class JobProfile:
    def __init__(self, title: str, description: str, skills: List[str], preferences: dict):
        self.title = title
        self.description = description
        self.skills = skills
        self.preferences = preferences

    def __repr__(self):
        return f"JobProfile(title={self.title}, skills={self.skills})"

    def to_dict(self):
        return {
            "title": self.title,
            "description": self.description,
            "skills": self.skills,
            "preferences": self.preferences
        }