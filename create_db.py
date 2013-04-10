from flatterer import app, db
from flatterer.models import Time, Gender

db.create_all()

db.session.add(Gender("Male"))
db.session.add(Gender("Female"))
db.session.add(Gender("Any"))
db.session.add(Gender("None"))

for i in range(6, 12):
    db.session.add(Time("May 17th, "+str(i)+":00 PM"))
db.session.add(Time("May 18th, 12:00 AM"))
for i in range(1, 9):
    db.session.add(Time("May 18th, "+str(i)+":00 AM"))

#import existingdb

db.session.commit()


