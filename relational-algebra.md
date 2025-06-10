### From passenger-dashboard.sql

1. **Trip Request Information**

```math
\pi_{id}(
    \sigma_{passenger\_id = \$1 \land trip\_status = 'pending'}(
        trips
    )
)
```

### From driver-dashboard.sql

2. **Nearby Trip Requests**

```math
\pi_{\substack{trip\_id, start\_location, end\_location, \\ trip\_type, passenger\_name, distance}}(
    \sigma_{\substack{trip\_status = 'pending' \land \\ ST\_DWithin(start\_location, ST\_MakePoint(\$1, \$2), 5000)}}(
        trips \bowtie_{trips.passenger\_id = users.id} users
    )
)
```

### From admin-dashboard.sql

3. **Pending Driver Applications**

```math
\pi_{\substack{application\_id, name, phone, \\ status, document\_type, file\_path}}(
    \sigma_{da.status = 'pending'}(
        driver\_applications \bowtie users \\
        \bowtie_{u.id = d.user\_id} documents \\
        \bowtie_{d.file\_id = f.id} files
    )
)
```

4. **Transactions in Date Range**

```math
\pi_{\substack{transaction\_id, user\_name, \\ amount, type, date}}(
    \sigma_{date \geq \$1 \land date \leq \$2}(
        transactions \bowtie_{t.user\_id = u.id} users
    )
)
```

5. **Active Drivers' Locations**

```math
\pi_{\substack{driver\_name, driver\_id, \\ location, recorded\_at}}(
    \sigma_{recorded\_at > now() - INTERVAL '5 minutes'}(
        driver\_locations \bowtie drivers \\
        \bowtie_{d.user\_id = u.id} users
    )
)
```

6. **Monthly Trip Count per Passenger**

```math
\gamma_{\substack{u.id, u.name, \\ COUNT(t.id) AS monthly\_trip\_count}}(
    \sigma_{\substack{trip\_status = 'completed' \land \\ start\_time \geq date\_trunc('month', CURRENT\_DATE)}}(
        trips \bowtie_{t.passenger\_id = u.id} users
    )
)
```

7. **Top 10 Passengers by Payment**

```math
\tau_{total\_payment DESC}(
    \gamma_{\substack{u.id, u.name, \\ SUM(p.amount) AS total\_payment}}(
        \sigma_{p.status = 'completed'}(
            payments \bowtie trips \\
            \bowtie_{t.passenger\_id = u.id} users
        )
    )
)[0:9]
```

8. **Active Drivers Report**

```math
\gamma_{\substack{d.user\_id, u.name, \\ COUNT(t.id), \\ SUM(CASE WHEN t.trip\_type = 'urban' THEN 1 ELSE 0 END), \\ SUM(CASE WHEN t.trip\_type = 'intercity' THEN 1 ELSE 0 END), \\ AVG(f.rating)}}(
    drivers \bowtie users \\
    \bowtie_{\substack{d.user\_id = t.driver\_id \land \\ t.trip\_status = 'completed'}} trips \\
    \bowtie_{t.id = f.trip\_id} feedbacks
)
```

9. **Trip Routes Report** (from 3.8)

```math
\gamma_{\substack{route\_id, \\ EXTRACT(HOUR FROM start\_time), \\ COUNT(id)}}(
    \sigma_{route\_id IS NOT NULL}(
        trips
    )
)
```
