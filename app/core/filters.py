from rest_framework import filters
from django.db.models import Q

class GenericQueryParameterListFilter(filters.BaseFilterBackend):
    """
    Custom filter backend to handle dynamic filtering based on query parameters
    formatted as filter[parameter]=value. Supports filtering on regular fields,
    ManyToMany fields, and ForeignKey fields.
    """
    def filter_queryset(self, request, queryset, view):
        """
        Main method to filter the queryset based on the request's query parameters.

        Args:
            request: The HTTP request object containing query parameters.
            queryset: The initial queryset to be filtered.
            view: The view instance that called this filter.

        Returns:
            The filtered queryset.
        """
        # Retrieve the list of fields that can be filtered from the view
        filterset_fields = getattr(view, 'filterset_fields', None)
        
        # If there are no filterable fields defined, return the original queryset
        if not filterset_fields:
            return queryset

        # Iterate through each field defined in filterset_fields
        for field in filterset_fields:
            # Check if the query parameter for this field is present in the request
            filter_param = request.query_params.get(f'filter[{field}]', None)
            if filter_param:
                # Split the parameter values by comma to support multiple values
                filter_values = filter_param.split(',')
                # Apply the filter to the queryset using the appropriate strategy
                queryset = self.apply_filter(queryset, field, filter_values)
                
        return queryset

    def apply_filter(self, queryset, field, filter_values):
        """
        Apply the appropriate filter to the queryset based on the field type.

        Args:
            queryset: The initial queryset to be filtered.
            field: The field name to filter on.
            filter_values: The list of values to filter by.

        Returns:
            The filtered queryset.
        """
        # Determine if the field is a related field (ManyToMany or ForeignKey)
        if self.is_related_field(field, queryset.model):
            # Build queries for related fields
            queries = self.build_related_field_queries(field, filter_values)
        else:
            # Build queries for regular fields
            queries = self.build_regular_field_queries(field, filter_values)
        # Filter the queryset using the constructed queries
        return queryset.filter(queries)

    def build_related_field_queries(self, field, filter_values):
        """
        Construct Q objects for related fields (ManyToMany or ForeignKey).

        Args:
            field: The field name to filter on.
            filter_values: The list of values to filter by.

        Returns:
            A Q object representing the combined queries.
        """
        queries = Q()
        for value in filter_values:
            # Construct Q object for each value and combine with OR operator
            queries |= Q(**{f"{field}__id": value})
        return queries

    def build_regular_field_queries(self, field, filter_values):
        """
        Construct a Q object for regular fields.

        Args:
            field: The field name to filter on.
            filter_values: The list of values to filter by.

        Returns:
            A Q object representing the filter.
        """
        # Use IN lookup for filtering regular fields
        return Q(**{f"{field}__in": filter_values})

    def is_related_field(self, field, model):
        """
        Determine if a field is a related field (ManyToMany or ForeignKey).

        Args:
            field: The field name to check.
            model: The model class being queried.

        Returns:
            True if the field is a related field, False otherwise.
        """
        many_to_many_fields = [f.name for f in model._meta.many_to_many]
        foreign_key_fields = [f.name for f in model._meta.fields if f.many_to_one]
        return field in many_to_many_fields or field in foreign_key_fields
