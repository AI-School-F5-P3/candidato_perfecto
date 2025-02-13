class RankingCreator:
    def __init__(self):
        pass

    def create_ranking_dataframe(self, rankings) -> pd.DataFrame:
        """Convert the ranking to a pandas DataFrame for visualization"""
        try:
            data = []
            for candidate, scores in rankings:
                # Pre-format all score values at creation time
                row = {
                    'Nombre Candidato': candidate.nombre_candidato,
                    'Estado': 'Descalificado' if scores.get('disqualified', False) else 'Calificado',
                    'Score Final': f"{scores['final_score']:.1%}",
                    'Score Habilidades': f"{scores['component_scores']['habilidades']:.1%}",
                    'Score Experiencia': f"{scores['component_scores']['experiencia']:.1%}",
                    'Score Formación': f"{scores['component_scores']['formacion']:.1%}",
                    'Score Preferencias': f"{scores['component_scores']['preferencias_reclutador']:.1%}",
                    'Habilidades': ', '.join(candidate.habilidades[:5]) + ('...' if len(candidate.habilidades) > 5 else ''),
                    'Experiencia': ', '.join(candidate.experiencia[:3]) + ('...' if len(candidate.experiencia) > 3 else ''),
                    'Formación': ', '.join(candidate.formacion[:2]) + ('...' if len(candidate.formacion) > 2 else ''),
                    'Razones Descalificación': ', '.join(scores.get('disqualification_reasons', [])) or 'N/A',
                    'raw_data': candidate.raw_data
                }
                data.append(row)
            
            df = pd.DataFrame(data)
            
            # Sort by Estado (qualified first) and then by Score Final
            df['Sort Score'] = df['Score Final'].str.rstrip('%').astype('float')
            df = df.sort_values(
                by=['Estado', 'Sort Score'], 
                ascending=[True, False],  # True for Estado to put 'Calificado' first
                key=lambda x: x if x.name != 'Estado' else pd.Categorical(x, ['Calificado', 'Descalificado'])
            )
            df = df.drop('Sort Score', axis=1)
            
            logging.info("Ranking DataFrame created successfully.")
            return df
        except Exception as e:
            logging.error(f"Error creating ranking DataFrame: {str(e)}")
            raise e