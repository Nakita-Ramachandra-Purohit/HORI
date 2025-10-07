import os, datetime as dt, random, psycopg2
DSN = os.getenv("DB_DSN","dbname=postgres user=postgres password=postgres host=postgres port=5432")

def insert_demo():
    conn = psycopg2.connect(DSN); cur = conn.cursor()
    now = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc)
    # Write a few observations around a fixed area
    for i in range(-2,3):
        ts = now + dt.timedelta(minutes=i*5)
        temp = 20 + random.uniform(-3,3)
        aqi  = int(80 + random.uniform(-20,60))
        cur.execute("INSERT INTO observations(lat,lon,ts,temp_c,aqi) VALUES (%s,%s,%s,%s,%s)",
                    (39.96,-75.60, ts, temp, aqi))
        # forecasts +15..+60 minutes
        fts = now + dt.timedelta(minutes=15 + i*10)
        ftemp = temp + random.uniform(-1,1)
        faq   = max(0, aqi + random.randint(-10,20))
        cur.execute("INSERT INTO forecasts(lat,lon,ts,temp_c,aqi) VALUES (%s,%s,%s,%s,%s)",
                    (39.96,-75.60, fts, ftemp, faq))
    conn.commit(); cur.close(); conn.close()

if __name__=="__main__":
    insert_demo()
    print("Inserted demo obs/forecasts")
