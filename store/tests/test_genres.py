import pytest
from model_bakery import baker
from rest_framework import status
from store.models import Genre


@pytest.mark.django_db
class TestRetrieveGenres:
    def test_if_genre_exists_return_200(self, api_client):
        # AAA (Arrange, Act, Assert)
        # Arrange

        # Act: where we kick off the behaviour that we wanna test
        # send request to the server
        genre = baker.make(Genre)
        # print(genre.__dict__)
        # {'_state': <django.db.models.base.ModelState object at 0x1037e7200>, 'id': 1, 'title': 'qyOHlFpWGSToBpHdBLQzSunotnzlfjOYbKRwiXSzpzvqcezmCfNOfntqgSdqhqaxXQLLFSgfbAQcgydDLYpHIdKVPQUxsELcNbuiYGidqMrmyiAoIcOeUvOjGYCugZKmLWYwMJQskQiNnIBXHGxNoLvEvdvFppGLxCzrKcWqxUuEnxJOAqcNqiGiAkPsfmknuRWarbXpBzpoAuwBEZltRVJukGtqmkjpPGtRAJErZueykfangPFHOlisKsiqilc', 'slug': 'TklJapxWT30ck8kpjHABx4RamixwbFw0DIQOsTru4Y5MP3E_qk'}
        response = api_client.get(f'/store/genres/{genre.id}/')

        # Assert: check to see if the behaviour happens or not
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == genre.id
        assert response.data['title'] == genre.title
        assert response.data['videos_count'] == 0
        # assert response.data == {
        #     'id': genre.id,
        #     'title': genre.title,
        #     'videos_count': 0,
        # }
