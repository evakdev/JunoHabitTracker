from models import MethodBase
from datetime import timedelta

class EverydayMethod(MethodBase):
    @property
    def streak(self, user, habit):
        records = self.get_records(user,habit)
        streak = 0
        for ind,record in enumerate(records):
            if ind ==0:
                streak+=1
                continue
            if records[ind-1].date-timedelta(days=1)==record.date:
                streak+=1
            else:
                return streak

