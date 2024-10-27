from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets, permissions

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

    def get_permissions(self):
        if self.action == "list":
            return (permissions.AllowAny(),)
        return (permissions.IsAdminUser(),)

    @extend_schema(
        summary="Get list of books",
        description="Return list of books, "
                    "filtered by title, author and cover",
        responses={200: BookListSerializer(many=True)},
        parameters=[
            OpenApiParameter(
                name="title",
                type={"type": "array", "items": {"type": "string"}},
                description="Filter books by title (ex. ?title=It)",
            ),
            OpenApiParameter(
                name="author",
                type={"type": "array", "items": {"type": "string"}},
                description="Filter books by author "
                            "(ex. ?author=Stephen King)",
            ),
            OpenApiParameter(
                name="cover",
                type={"type": "string", "enum": ["Hard", "Soft"]},
                description="Filter books by cover (ex. ?cover=Hard)",
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
