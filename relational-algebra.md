### Passenger Information

1. **Trip History (Completed or Canceled)**

```math
\sigma_{(passenger\_id = \$passenger\_id) \land (trip\_status = 'completed' \lor trip\_status = 'canceled')}(trips)
```

2. **Payments**

```math
\pi_{p.*}(
    \sigma_{t.passenger\_id = \$passenger\_id}(
        trips \bowtie_{t.payment\_id = p.id} payments
    )
)
```

3. **Messages**

```math
\sigma_{(sender\_id = \$passenger\_id \lor receiver\_id = \$passenger\_id)}(messages)
```

4. **Feedback and Ratings**

```math
\sigma_{(giver\_id = \$passenger\_id \lor receiver\_id = \$passenger\_id)}(feedbacks)
```

5. **Wallet Balance**

```math
\pi_{wallet\_balance}(
    \sigma_{id = \$passenger\_id}(users)
)
```

6. **Assigned Discount Codes**

```math
\pi_{dc.*}(
    \sigma_{(du.user\_id = \$passenger\_id) \land (dc.status = 'used' \lor dc.status = 'expired')}(
        discount\_user \bowtie_{du.discount\_code\_id = dc.id} discount\_codes
    )
)
```

### Financial Transactions

7. **All Transactions with Payment Type**

```math
\pi_{t.*, p.payment\_type}(
    transactions \bowtie_{t.payment\_id = p.id} payments
)
```

### Trip Information

8. **Urban Trips**

```math
\sigma_{trip\_type = 'urban'}(trips)
```

9. **Intercity Trips**

```math
\sigma_{trip\_type = 'intercity'}(trips)
```

10. **Return Trips**

```math
\pi_{t.*}(
    (\sigma_{is\_return = TRUE}(routes)) \bowtie_{r.id = t.route\_id} trips
)
```

### Driver Applications

11. **Applicant Profile and Status**

```math
\pi_{u.name, da.status, da.comments, d.type, d.status}(
    \sigma_{da.user\_id = \$applicant\_id}(
        driver\_applications \bowtie_{da.user\_id = u.id} users \\
        \bowtie_{u.id = d.user\_id} documents
    )
)
```

### City and Route Information

12. **Covered Cities**

```math
\pi_{name, province\_id}(
    \sigma_{coverage\_status = TRUE}(cities)
)
```

13. **Routes with City Names**

```math
\pi_{r.id, start\_city.name, end\_city.name}(
    routes \bowtie_{r.start\_city\_id = start\_city.id} cities\ AS\ start\_city \\
    \bowtie_{r.end\_city\_id = end\_city.id} cities\ AS\ end\_city
)
```

### Admin Information

14. **Admin Profile**

```math
\pi_{u.name, u.email, a.access\_level}(
    \sigma_{u.id = \$admin\_id}(
        users \bowtie_{u.id = a.user\_id} admins
    )
)
```

### Combined with Original Queries

15. **Nearby Trip Requests** (from driver-dashboard.sql)

```math
\pi_{\substack{trip\_id, start\_location, end\_location, \\ trip\_type, passenger\_name, distance}}(
    \sigma_{\substack{trip\_status = 'pending' \land \\ ST\_DWithin(start\_location, ST\_MakePoint(\$1, \$2), 5000}}(
        trips \bowtie_{trips.passenger\_id = users.id} users
    )
)
```

16. **Active Drivers Report** (from admin-dashboard.sql)

```math
\gamma_{\substack{d.user\_id, u.name, \\ COUNT(t.id), \\ SUM(CASE\ WHEN\ t.trip\_type = 'urban'\ THEN\ 1\ ELSE\ 0\ END), \\ SUM(CASE\ WHEN\ t.trip\_type = 'intercity'\ THEN\ 1\ ELSE\ 0\ END), \\ AVG(f.rating)}}(
    drivers \bowtie users \\
    \bowtie_{\substack{d.user\_id = t.driver\_id \land \\ t.trip\_status = 'completed'}} trips \\
    \bowtie_{t.id = f.trip\_id} feedbacks
)
```
