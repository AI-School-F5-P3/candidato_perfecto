class CandidateProfile:
    def __init__(self, nombre_candidato, habilidades, experiencia, formacion, raw_data):
        self.nombre_candidato = nombre_candidato
        self.habilidades = habilidades
        self.experiencia = experiencia
        self.formacion = formacion
        self.raw_data = raw_data

    def __repr__(self):
        return f"CandidateProfile(nombre_candidato={self.nombre_candidato}, habilidades={self.habilidades}, experiencia={self.experiencia}, formacion={self.formacion})"