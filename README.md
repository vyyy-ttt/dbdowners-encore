# Encore

**Rate every layer of a live show: the artist, the openers, and the venue itself.**

When you buy anything online you check the reviews first, but when you buy a
concert ticket you are flying blind. A great artist can be let down by a bad
room, and an opener you have never heard of can be the best part of the night.
Most platforms collapse the whole evening into a single star rating, or treat a
venue like any other business listing.

Encore keeps those things separate. Concertgoers review the **show**, the
**venue**, and the **artist** independently, tag what actually went wrong or
right, and build up a history of everything they have been to. That same
structured feedback is what venue staff and tour managers need and currently
cannot get: which gate is backing up, whether the sound is the room or the mix,
and which cities are worth returning to.

CS 3200, Summer B 2026 — Database Design Project, Phase 3.

## Team DBDowners

| Name | Email |
| --- | --- |
| Vy Truong | truong.vy@northeastern.edu |
| Sargun Kaur | kaur.sar@northeastern.edu |
| Nilesh Thakur | thakur.nil@northeastern.edu |

## Demo video

**TODO: paste the public link here before submitting.** It must be viewable by
anyone with the link — if a grader has to request access, the demo scores zero.

## User personas

| Persona | Who they are | What the app gives them |
| --- | --- | --- |
| **Maya** | Casual concertgoer | Logs shows she attends, reviews the artist, venue and night, follows friends |
| **Teddy** | Venue manager at Fenway Park | Structured feedback about his room, broken down by category |
| **Enrica** | Tour manager | Fan sentiment stop by stop, and a way to respond on behalf of the artist |
| **Andy** | App administrator | Reports queue, venue and artist listings, user moderation |

Each persona has a landing page plus three feature pages:

| Persona | Feature pages | User stories covered |
| --- | --- | --- |
| **Maya** | Log & Review · My Profile · Search Shows | 1.1, 1.2, 1.3, 1.4, 1.5, 1.6 |
| **Teddy** | Venue Overview · Venue Reviews · Venue Details | 2.1, 2.2, 2.3, 2.4, 2.5, 2.6 |
| **Enrica** | Tour Insights · Tour Reviews · Tour Performance | 3.1, 3.2, 3.3, 3.4, 3.5, 3.6 |
| **Andy** | Manage Reports · Manage Venues · Manage Users | 4.1, 4.2, 4.3, 4.4, 4.5, 4.6 |


## Running the project

### Prerequisites

[Docker Desktop](https://www.docker.com/products/docker-desktop/). Everything
else runs inside containers. See [docs/PreReq.md](docs/PreReq.md) if you also
want a local Python environment for editor support.

### 1. Create the environment file

The API reads its database credentials from `api/.env`, which is **not** in the
repo. Copy the template and fill in the two placeholder values:

```bash
cp api/.env.template api/.env
```

```
SECRET_KEY=<change-this-to-a-random-secret>
DB_USER=root
DB_HOST=db
DB_PORT=3306
DB_NAME=encore
MYSQL_ROOT_PASSWORD=<change-this-to-a-strong-password>
```

`MYSQL_ROOT_PASSWORD` is used both to create the database container and to
connect to it, so the same value has to appear only once here.

### 2. Start everything

```bash
docker compose up -d
```

| Service | Container | URL |
| --- | --- | --- |
| Streamlit app | `web-app` | http://localhost:8501 |
| Flask REST API | `web-api` | http://localhost:4000 |
| MySQL | `mysql_db` | `localhost:3200` |

Open **http://localhost:8501** and pick a persona. There is no login; each
button just switches which view of the app you see.

### 3. Resetting the database

Every `.sql` file in `database-files/` runs **only when the database container
is first created**, in alphabetical order. Restarting an existing container will
not re-run them. To pick up schema or data changes:

```bash
docker compose down -v && docker compose up -d
```

The `-v` is the important part — it deletes the volume holding the old data.

## Repository layout

| Path | Contents |
| --- | --- |
| `app/` | Streamlit front end |
| `api/` | Flask REST API, one blueprint per resource |
| `database-files/` | `ddl.sql` (schema + seed rows), `zz_mock_data.sql` (sample data) |
| `docs/` | Project documentation |

## The REST API

Routes are split into one Flask blueprint per resource, under `api/backend/`.

| Blueprint | Prefix | Routes |
| --- | --- | --- |
| `followers` | `/follower` | 5 |
| `maya` | `/maya` | 9 |
| `reports` | `/report` | 5 |
| `reviews` | `/review` | 6 |
| `tags` | `/tag` | 5 |
| `tours` | `/tour` | 7 |
| `transportations` | `/transport` | 6 |
| `users` | `/user` | 5 |
| `venue_managers` | `/venue_manager` | 6 |
| `venues` | `/venue` | 10 |

64 routes in total, using all four HTTP verbs.

## Sample data

`database-files/zz_mock_data.sql` is generated with the Python
[Faker](https://faker.readthedocs.io/) library from a fixed random seed, so
regenerating produces identical rows. Row counts follow the Phase 3 guidance:

- **40 rows** per strong entity (`user`, `artist`, `venue`, `tour`, `tag`, …)
- **75 rows** per weak entity (`show`, `review`, `report`, `transportation`, …)
- **150 rows** per bridge table (`follows`, `review_tag`, `user_show`, …)

`ddl.sql` seeds rows 1–4 of every table by hand so the personas have known
identities, which is why the generated file starts its ids at 5 and sorts after
`ddl.sql` alphabetically.
