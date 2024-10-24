from rest_framework import viewsets

from books.models import Book
from books.serializers import BookSerializer, BookListSerializer


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

    def get_queryset(self):
        queryset = self.queryset

        title = self.request.query_params.get("title", None)
        author = self.request.query_params.get("author", None)
        cover = self.request.query_params.get("cover", None)
        if title:
            queryset = queryset.filter(title__icontains=title)

        if author:
            queryset = queryset.filter(author__icontains=author)

        if cover:
            queryset = queryset.filter(cover__icontains=cover)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return BookListSerializer
        return BookSerializer
