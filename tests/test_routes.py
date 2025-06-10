def test_db_is_in_memory(app_fixture):
    uri = app_fixture.config['SQLALCHEMY_DATABASE_URI']
    assert uri == 'sqlite:///:memory:'

def test_home_page(app_fixture):
    with app_fixture.test_client() as test_client:
        response = test_client.get('/')
        assert response.status_code == 200
        assert b"Strava" in response.data

def test_not_found(app_fixture):
    with app_fixture.test_client() as test_client:
        response = test_client.get('/thisdoesntexist')
        assert response.status_code == 404
        assert b"Page not found" in response.data

def test_full_workflow(client):
    # User registration
    response = client.post('/register', data={
        'username': 'testuser',
        'password': 'testpass'
    })
    assert response.status_code in (200, 302)

    # User login
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'testpass'
    })
    assert response.status_code in (200, 302)

    # User profile access
    response = client.get('/profile')
    assert response.status_code in (200, 302)

    # Change password (user must be logged in)
    response = client.post('/profile/password', data={
        'old_password': 'testpass',
        'new_password': 'newpass123',
        'new_password2': 'newpass123'
    }, follow_redirects=True)
    assert response.status_code == 200

    # Logout after password change
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200

    # Login with new password should succeed
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'newpass123'
    }, follow_redirects=True)
    assert response.status_code == 200

    # anonymous user access on restricted page
    response = client.get('/profile')
    assert response.status_code in (302, 401, 403)
