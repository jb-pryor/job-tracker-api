def authenticate(client, email):
    """Create a test account and return its authentication header."""
    password = "a-long-practice-password"

    registration = client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )
    assert registration.status_code == 201

    login = client.post(
        "/auth/token",
        data={"username": email, "password": password},
    )
    assert login.status_code == 200

    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_application(client):
    headers = authenticate(client, "creator@example.com")

    response = client.post(
        "/applications",
        headers=headers,
        json={
            "company": "Example Company",
            "job_title": "Junior Software Engineer",
        },
    )

    assert response.status_code == 201

    application = response.json()
    assert isinstance(application["id"], int)
    assert application["company"] == "Example Company"
    assert application["job_title"] == "Junior Software Engineer"
    assert application["status"] == "saved"

    # Retrieve it to verify it was saved.
    fetched = client.get(
        f"/applications/{application['id']}",
        headers=headers,
    )

    assert fetched.status_code == 200
    assert fetched.json()["id"] == application["id"]
    assert fetched.json()["company"] == "Example Company"


def test_create_application_requires_authentication(client):
    response = client.post(
        "/applications",
        json={
            "company": "Example Company",
            "job_title": "Junior Software Engineer",
        },
    )

    assert response.status_code == 401


def test_create_application_rejects_blank_company(client):
    headers = authenticate(client, "validation@example.com")

    response = client.post(
        "/applications",
        headers=headers,
        json={
            "company": "   ",
            "job_title": "Junior Software Engineer",
        },
    )

    assert response.status_code == 422

    # Rejected input should not create a record.
    listing = client.get("/applications", headers=headers)

    assert listing.status_code == 200
    assert listing.json()["total"] == 0
    assert listing.json()["items"] == []


def test_other_user_cannot_read_application(client):
    owner_headers = authenticate(client, "owner@example.com")
    other_headers = authenticate(client, "other@example.com")

    created = client.post(
        "/applications",
        headers=owner_headers,
        json={
            "company": "Example Company",
            "job_title": "Junior Software Engineer",
        },
    )
    assert created.status_code == 201
    application_id = created.json()["id"]

    # Another user cannot retrieve the owner's application.
    response = client.get(
        f"/applications/{application_id}",
        headers=other_headers,
    )
    assert response.status_code == 404

    # It must not appear in that user's list either.
    listing = client.get(
        "/applications",
        headers=other_headers,
    )

    assert listing.status_code == 200
    assert listing.json()["total"] == 0
    assert listing.json()["items"] == []

    # The owner can still access it.
    owner_response = client.get(
        f"/applications/{application_id}",
        headers=owner_headers,
    )
    assert owner_response.status_code == 200



def test_update_application(client):
    headers = authenticate(client, "update@example.com")

    created = client.post(
        "/applications",
        headers=headers,
        json={
            "company": "Example Company",
            "job_title": "Junior Software Engineer",
            "notes": "Original notes",
        },
    )
    assert created.status_code == 201
    application_id = created.json()["id"]

    updated = client.patch(
        f"/applications/{application_id}",
        headers=headers,
        json={"status": "applied", "notes": None},
    )

    assert updated.status_code == 200

    # Fetch again to verify the changes were saved.
    fetched = client.get(
        f"/applications/{application_id}",
        headers=headers,
    )
    assert fetched.status_code == 200

    application = fetched.json()
    assert application["status"] == "applied"
    assert application["notes"] is None
    assert application["company"] == "Example Company"
    assert application["job_title"] == "Junior Software Engineer"


def test_delete_application(client):
    headers = authenticate(client, "delete@example.com")

    created = client.post(
        "/applications",
        headers=headers,
        json={
            "company": "Example Company",
            "job_title": "Junior Software Engineer",
        },
    )
    assert created.status_code == 201
    application_id = created.json()["id"]

    deleted = client.delete(
        f"/applications/{application_id}",
        headers=headers,
    )

    assert deleted.status_code == 204
    assert deleted.content == b""

    fetched = client.get(
        f"/applications/{application_id}",
        headers=headers,
    )
    assert fetched.status_code == 404

    # Deleting the same record again should report that it is missing.
    repeated = client.delete(
        f"/applications/{application_id}",
        headers=headers,
    )
    assert repeated.status_code == 404


def test_other_user_cannot_update_or_delete_application(client):
    owner_headers = authenticate(client, "protected-owner@example.com")
    other_headers = authenticate(client, "protected-other@example.com")

    created = client.post(
        "/applications",
        headers=owner_headers,
        json={
            "company": "Example Company",
            "job_title": "Junior Software Engineer",
        },
    )
    assert created.status_code == 201
    application_id = created.json()["id"]

    updated = client.patch(
        f"/applications/{application_id}",
        headers=other_headers,
        json={"status": "rejected"},
    )
    assert updated.status_code == 404

    deleted = client.delete(
        f"/applications/{application_id}",
        headers=other_headers,
    )
    assert deleted.status_code == 404

    # Verify both attempts left the owner's record intact.
    fetched = client.get(
        f"/applications/{application_id}",
        headers=owner_headers,
    )

    assert fetched.status_code == 200
    assert fetched.json()["status"] == "saved"
    assert fetched.json()["company"] == "Example Company"



def test_filter_applications_by_status(client):
    headers = authenticate(client, "filter@example.com")
    other_headers = authenticate(client, "filter-other@example.com")

    application_ids = {}

    for status in ["saved", "applied", "interviewing"]:
        created = client.post(
            "/applications",
            headers=headers,
            json={
                "company": f"Company {status}",
                "job_title": "Junior Software Engineer",
                "status": status,
            },
        )
        assert created.status_code == 201
        application_ids[status] = created.json()["id"]

    # Another user's matching application must be excluded.
    other_created = client.post(
        "/applications",
        headers=other_headers,
        json={
            "company": "Other Company",
            "job_title": "Junior Software Engineer",
            "status": "applied",
        },
    )
    assert other_created.status_code == 201

    response = client.get(
        "/applications",
        headers=headers,
        params={"status": "applied"},
    )

    assert response.status_code == 200
    result = response.json()

    assert result["total"] == 1
    assert len(result["items"]) == 1
    assert result["items"][0]["id"] == application_ids["applied"]
    assert result["items"][0]["status"] == "applied"

    # A valid status with no matches should return an empty list.
    empty = client.get(
        "/applications",
        headers=headers,
        params={"status": "offer"},
    )

    assert empty.status_code == 200
    assert empty.json()["total"] == 0
    assert empty.json()["items"] == []


def test_application_pagination(client):
    headers = authenticate(client, "pagination@example.com")
    created_ids = []

    for number in range(3):
        created = client.post(
            "/applications",
            headers=headers,
            json={
                "company": f"Company {number}",
                "job_title": "Junior Software Engineer",
            },
        )
        assert created.status_code == 201
        created_ids.append(created.json()["id"])

    # Your endpoint sorts newest first.
    expected_ids = list(reversed(created_ids))

    first_page = client.get(
        "/applications",
        headers=headers,
        params={"limit": 2, "offset": 0},
    )

    assert first_page.status_code == 200
    first = first_page.json()

    assert first["total"] == 3
    assert first["limit"] == 2
    assert first["offset"] == 0
    assert [item["id"] for item in first["items"]] == expected_ids[:2]

    second_page = client.get(
        "/applications",
        headers=headers,
        params={"limit": 2, "offset": 2},
    )

    assert second_page.status_code == 200
    second = second_page.json()

    assert second["total"] == 3
    assert second["offset"] == 2
    assert [item["id"] for item in second["items"]] == expected_ids[2:]

    beyond_last_page = client.get(
        "/applications",
        headers=headers,
        params={"limit": 2, "offset": 3},
    )

    assert beyond_last_page.status_code == 200
    assert beyond_last_page.json()["total"] == 3
    assert beyond_last_page.json()["items"] == []


def test_application_list_rejects_invalid_parameters(client):
    headers = authenticate(client, "invalid-query@example.com")

    invalid_parameters = [
        {"limit": 0},
        {"limit": 101},
        {"offset": -1},
        {"status": "unknown"},
    ]

    for parameters in invalid_parameters:
        response = client.get(
            "/applications",
            headers=headers,
            params=parameters,
        )

        assert response.status_code == 422, (
            f"Expected rejection for {parameters}, "
            f"got {response.status_code}"
        )