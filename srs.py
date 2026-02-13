from datetime import datetime, timedelta

class SRSManager:
    @staticmethod
    def calculate_next_review(stage, quality):
        if quality < 3:
            new_stage = max(0, stage - 2)
            days = 0.25
        else:
            new_stage = stage + 1
            
            if new_stage == 1:
                days = 1
            elif new_stage == 2:
                days = 3
            elif new_stage == 3:
                days = 7
            elif new_stage == 4:
                days = 14
            elif new_stage >= 5:
                days = 30
                new_stage = 5
            else:
                days = 0
                
            if quality == 3:
                days = days * 0.8
            elif quality == 4:
                days = days * 1.0
            elif quality == 5:
                days = days * 1.2
        
        return new_stage, days