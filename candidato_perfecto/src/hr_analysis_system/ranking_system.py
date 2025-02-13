class RankingSystem:
    def __init__(self, matching_engine):
        self.matching_engine = matching_engine

    async def rank_candidates(self, job_profile, candidate_profiles, killer_criteria=None):
        rankings = []
        for candidate in candidate_profiles:
            score = await self.matching_engine.match(job_profile, candidate, killer_criteria)
            rankings.append((candidate, score))
        return rankings