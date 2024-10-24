from rest_framework import serializers

from books.models import Book


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ("title", "author", "cover", "inventory", "daily_fee")


class BookListSerializer(BookSerializer):
    class Meta(BookSerializer.Meta):
        fields = ("title", "author", "cover")
