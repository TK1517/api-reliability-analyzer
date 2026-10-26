# Viva Questions and Answers

1. **What problem does the project solve?** It measures API response time and expected-status success, stores history, and provides analytics.
2. **Why Python?** It has a clear HTTP ecosystem and libraries for data analysis, testing, and dashboards.
3. **What does `requests` do?** It sends HTTP requests and exposes status, timing context, headers, and response content.
4. **What is an HTTP status code?** A server response code describing the outcome category of an HTTP request.
5. **Is HTTP 404 a transport failure?** No. It is an HTTP response, but is treated as unsuccessful under the default 200–299 success interval.
6. **Why use a monotonic clock?** It measures elapsed duration without being affected by system clock adjustments.
7. **Why store timestamps in UTC?** It avoids ambiguity across time zones and makes historical comparisons consistent.
8. **What is a timeout?** A limit on how long the client waits for connection or response activity.
9. **Connect timeout vs read timeout?** Connect timeout applies while establishing a connection; read timeout applies while waiting for response data.
10. **Why can status be null?** No HTTP response may have arrived due to a timeout, DNS, or connection error.
11. **What is SQLite?** An embedded relational database stored in a local file.
12. **Why SQLite for this project?** It needs no server and is sufficient for a small local academic workload.
13. **What is a foreign key?** A constraint linking a row to a valid row in another table.
14. **Why parameterized SQL?** It separates data from SQL syntax and helps prevent SQL injection.
15. **Why indexes?** They speed up common filtering and joining at the cost of extra storage and write work.
16. **What is normalization?** Organizing data to reduce duplication and preserve relationships.
17. **Why separate runs and logs?** A run records execution-level context; each log records one endpoint attempt.
18. **What is Pandas used for?** Tabular cleanup, grouping, filtering, and summary calculations.
19. **What is NumPy used for?** Numerical operations such as percentile calculation.
20. **Define success rate.** Successful attempts divided by all attempts, multiplied by 100.
21. **Define failure rate.** Failed attempts divided by all attempts, multiplied by 100.
22. **Why include failed attempts in reliability?** Excluding them would overstate reliability.
23. **Are all failed attempts included in latency summaries?** Only when elapsed time was measured; an absent latency is not invented as zero.
24. **What is a median?** The middle value after sorting observations; it is robust to extreme values.
25. **What is P95 latency?** A value at or below which approximately 95% of observed latency values fall under the selected percentile convention.
26. **Which percentile convention is used?** NumPy's linear interpolation convention.
27. **What is standard deviation?** A measure of dispersion around the mean; the implementation uses sample standard deviation for two or more values.
28. **What is anomaly detection?** Flagging observations that differ from a defined baseline or distribution rule.
29. **How does rolling median work?** It compares an observation with the median of preceding observations, avoiding use of the current point in its own baseline.
30. **What is IQR?** The third quartile minus the first quartile.
31. **How does IQR flag high latency?** It flags values above Q3 + k × IQR.
32. **What if IQR is zero?** The threshold equals Q3; values strictly above it are flagged, while equal values are not.
33. **Can an anomaly prove an outage?** No. It is a statistical signal that needs context.
34. **Why use threads?** HTTP monitoring is I/O-bound; threads can overlap network waiting time.
35. **Why bound concurrency?** It limits resource usage and avoids sending too many simultaneous requests.
36. **What is a future in `ThreadPoolExecutor`?** An object representing a submitted task and its eventual result or exception.
37. **How are worker failures handled?** The future is associated with its endpoint and unexpected worker exceptions become a failure record.
38. **Why compare sequential and concurrent runs?** It demonstrates the effect of overlapping I/O waits under a controlled workload.
39. **Why use a local test server?** It creates reproducible status, delay, and timeout scenarios without internet dependency.
40. **What is Streamlit?** A Python framework for building interactive data applications.
41. **What is Plotly used for?** Interactive charts with hover and zoom behavior.
42. **What is unit testing?** Testing an isolated function or component against expected behavior.
43. **What is integration testing?** Testing components working together, such as monitor plus SQLite.
44. **Why not call real public APIs in tests?** External availability and rate limits would make tests nondeterministic.
45. **What is SSRF?** Server-side request forgery, where an application is tricked into requesting unintended internal destinations.
46. **Why block private IPs?** Internal addresses can expose local services or network resources if arbitrary URLs are accepted.
47. **Why disable redirects?** A public URL could redirect to a private destination, bypassing a simple initial URL check.
48. **Does URL validation fully eliminate SSRF?** No. DNS rebinding and network routing require stronger network-level controls.
49. **Why do endpoint deletions with history fail?** The foreign-key constraint preserves referential integrity; disabling keeps history intact.
50. **What are the limitations?** It is manually triggered, has no alerting/authentication, and a small observation window cannot establish long-term uptime.
51. **Why no ML model?** Simple statistical rules are easier to explain and appropriate for a small educational dataset.
52. **What does response size measure?** The number of bytes exposed in the response content received by the client.
53. **Why not save response bodies?** They may contain sensitive or large content unnecessary for latency monitoring.
54. **Why are retries not automatic?** Retries can increase load and obscure the original failure; repeated checks should be intentional.
55. **How can the project be extended?** Add scheduling, alerting, authenticated endpoint profiles, retention controls, and network-level safeguards.
