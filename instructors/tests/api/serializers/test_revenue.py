from decimal import Decimal

from rest_framework import serializers

from instructors.api.serializers.revenue import (
    CourseBreakdownSerializer,
    PeriodRevenueSerializer,
    RevenueSerializer,
    RevenueSummarySerializer,
)


class TestPeriodRevenueSerializer:
    def test_declares_expected_fields(self):
        serializer = PeriodRevenueSerializer()

        assert set(serializer.fields) == {
            "value",
            "trend",
            "direction",
        }

    def test_value_is_decimal_field(self):
        serializer = PeriodRevenueSerializer()

        field = serializer.fields["value"]

        assert isinstance(field, serializers.DecimalField)
        assert field.max_digits == 14
        assert field.decimal_places == 2

    def test_trend_is_integer_field(self):
        serializer = PeriodRevenueSerializer()

        field = serializer.fields["trend"]

        assert isinstance(field, serializers.IntegerField)
        assert field.allow_null is True
        assert field.required is True

    def test_direction_is_char_field(self):
        serializer = PeriodRevenueSerializer()

        field = serializer.fields["direction"]

        assert isinstance(field, serializers.CharField)
        assert field.allow_null is True
        assert field.required is False

    def test_valid_data_is_accepted(self):
        serializer = PeriodRevenueSerializer(
            data={
                "value": "1250.50",
                "trend": 15,
                "direction": "up",
            }
        )

        assert serializer.is_valid()

        assert serializer.validated_data == {
            "value": Decimal("1250.50"),
            "trend": 15,
            "direction": "up",
        }

    def test_zero_revenue_is_accepted(self):
        serializer = PeriodRevenueSerializer(
            data={
                "value": "0.00",
                "trend": 0,
                "direction": "neutral",
            }
        )

        assert serializer.is_valid()

        assert serializer.validated_data["value"] == Decimal("0.00")

    def test_negative_revenue_is_accepted_by_serializer(self):
        """
        The serializer does not define a minimum-value validator.
        Any business rule about negative revenue belongs elsewhere.
        """
        serializer = PeriodRevenueSerializer(
            data={
                "value": "-125.50",
                "trend": -10,
                "direction": "down",
            }
        )

        assert serializer.is_valid()

        assert serializer.validated_data["value"] == Decimal("-125.50")

    def test_null_trend_is_accepted(self):
        serializer = PeriodRevenueSerializer(
            data={
                "value": "100.00",
                "trend": None,
                "direction": None,
            }
        )

        assert serializer.is_valid()

        assert serializer.validated_data["trend"] is None
        assert serializer.validated_data["direction"] is None

    def test_direction_can_be_omitted(self):
        serializer = PeriodRevenueSerializer(
            data={
                "value": "100.00",
                "trend": 10,
            }
        )

        assert serializer.is_valid()

        assert serializer.validated_data == {
            "value": Decimal("100.00"),
            "trend": 10,
        }

    def test_value_is_required(self):
        serializer = PeriodRevenueSerializer(
            data={
                "trend": 10,
                "direction": "up",
            }
        )

        assert not serializer.is_valid()
        assert "value" in serializer.errors

    def test_trend_is_required_even_though_nullable(self):
        serializer = PeriodRevenueSerializer(
            data={
                "value": "100.00",
                "direction": "up",
            }
        )

        assert not serializer.is_valid()
        assert "trend" in serializer.errors

    def test_value_does_not_allow_null(self):
        serializer = PeriodRevenueSerializer(
            data={
                "value": None,
                "trend": 10,
                "direction": "up",
            }
        )

        assert not serializer.is_valid()
        assert "value" in serializer.errors

    def test_trend_accepts_zero(self):
        serializer = PeriodRevenueSerializer(
            data={
                "value": "100.00",
                "trend": 0,
                "direction": "neutral",
            }
        )

        assert serializer.is_valid()
        assert serializer.validated_data["trend"] == 0

    def test_trend_accepts_negative_integer(self):
        serializer = PeriodRevenueSerializer(
            data={
                "value": "100.00",
                "trend": -25,
                "direction": "down",
            }
        )

        assert serializer.is_valid()
        assert serializer.validated_data["trend"] == -25

    def test_rejects_non_integer_trend(self):
        serializer = PeriodRevenueSerializer(
            data={
                "value": "100.00",
                "trend": "not-an-integer",
                "direction": "up",
            }
        )

        assert not serializer.is_valid()
        assert "trend" in serializer.errors

    def test_rejects_invalid_decimal_value(self):
        serializer = PeriodRevenueSerializer(
            data={
                "value": "not-a-decimal",
                "trend": 10,
                "direction": "up",
            }
        )

        assert not serializer.is_valid()
        assert "value" in serializer.errors

    def test_rejects_more_than_two_decimal_places(self):
        serializer = PeriodRevenueSerializer(
            data={
                "value": "1250.123",
                "trend": 10,
                "direction": "up",
            }
        )

        assert not serializer.is_valid()
        assert "value" in serializer.errors

    def test_accepts_maximum_decimal_capacity(self):
        serializer = PeriodRevenueSerializer(
            data={
                "value": "999999999999.99",
                "trend": 10,
                "direction": "up",
            }
        )

        assert serializer.is_valid()

        assert serializer.validated_data["value"] == Decimal("999999999999.99")

    def test_rejects_decimal_exceeding_max_digits(self):
        serializer = PeriodRevenueSerializer(
            data={
                "value": "1000000000000.00",
                "trend": 10,
                "direction": "up",
            }
        )

        assert not serializer.is_valid()
        assert "value" in serializer.errors

    def test_serializes_decimal_value_with_two_decimal_places(self):
        serializer = PeriodRevenueSerializer(
            instance={
                "value": Decimal("1250.50"),
                "trend": 15,
                "direction": "up",
            }
        )

        assert serializer.data == {
            "value": "1250.50",
            "trend": 15,
            "direction": "up",
        }

    def test_serializes_null_trend_and_direction(self):
        serializer = PeriodRevenueSerializer(
            instance={
                "value": Decimal("100.00"),
                "trend": None,
                "direction": None,
            }
        )

        assert serializer.data == {
            "value": "100.00",
            "trend": None,
            "direction": None,
        }

    def test_serializes_missing_optional_direction_as_null(self):
        serializer = PeriodRevenueSerializer(
            instance={
                "value": Decimal("100.00"),
                "trend": 5,
            }
        )

        assert serializer.data == {
            "value": "100.00",
            "trend": 5,
            "direction": None,
        }


class TestRevenueSummarySerializer:
    def test_declares_expected_fields(self):
        serializer = RevenueSummarySerializer()

        assert set(serializer.fields) == {
            "lifetime",
            "period_revenue",
            "ytd",
        }

    def test_nested_fields_are_period_revenue_serializers(self):
        serializer = RevenueSummarySerializer()

        assert isinstance(
            serializer.fields["lifetime"],
            PeriodRevenueSerializer,
        )
        assert isinstance(
            serializer.fields["period_revenue"],
            PeriodRevenueSerializer,
        )
        assert isinstance(
            serializer.fields["ytd"],
            PeriodRevenueSerializer,
        )

    def test_all_nested_fields_are_required(self):
        serializer = RevenueSummarySerializer()

        assert serializer.fields["lifetime"].required is True
        assert serializer.fields["period_revenue"].required is True
        assert serializer.fields["ytd"].required is True

    def test_valid_nested_data_is_accepted(self):
        data = {
            "lifetime": {
                "value": "5000.00",
                "trend": None,
                "direction": None,
            },
            "period_revenue": {
                "value": "1200.50",
                "trend": 20,
                "direction": "up",
            },
            "ytd": {
                "value": "8500.75",
                "trend": 10,
                "direction": "up",
            },
        }

        serializer = RevenueSummarySerializer(data=data)

        assert serializer.is_valid()

        assert serializer.validated_data["lifetime"]["value"] == Decimal("5000.00")
        assert serializer.validated_data["period_revenue"]["value"] == Decimal(
            "1200.50"
        )
        assert serializer.validated_data["ytd"]["value"] == Decimal("8500.75")

    def test_rejects_missing_lifetime(self):
        serializer = RevenueSummarySerializer(
            data={
                "period_revenue": {
                    "value": "1200.00",
                    "trend": 10,
                    "direction": "up",
                },
                "ytd": {
                    "value": "5000.00",
                    "trend": 5,
                    "direction": "up",
                },
            }
        )

        assert not serializer.is_valid()
        assert "lifetime" in serializer.errors

    def test_rejects_missing_period_revenue(self):
        serializer = RevenueSummarySerializer(
            data={
                "lifetime": {
                    "value": "1200.00",
                    "trend": 10,
                    "direction": "up",
                },
                "ytd": {
                    "value": "5000.00",
                    "trend": 5,
                    "direction": "up",
                },
            }
        )

        assert not serializer.is_valid()
        assert "period_revenue" in serializer.errors

    def test_rejects_missing_ytd(self):
        serializer = RevenueSummarySerializer(
            data={
                "lifetime": {
                    "value": "1200.00",
                    "trend": 10,
                    "direction": "up",
                },
                "period_revenue": {
                    "value": "500.00",
                    "trend": 5,
                    "direction": "up",
                },
            }
        )

        assert not serializer.is_valid()
        assert "ytd" in serializer.errors

    def test_rejects_invalid_nested_period_revenue(self):
        serializer = RevenueSummarySerializer(
            data={
                "lifetime": {
                    "value": "1200.00",
                    "trend": 10,
                    "direction": "up",
                },
                "period_revenue": {
                    "value": "invalid",
                    "trend": 5,
                    "direction": "up",
                },
                "ytd": {
                    "value": "500.00",
                    "trend": 5,
                    "direction": "up",
                },
            }
        )

        assert not serializer.is_valid()
        assert "period_revenue" in serializer.errors
        assert "value" in serializer.errors["period_revenue"]

    def test_allows_nullable_nested_trend_and_direction(self):
        data = {
            "lifetime": {
                "value": "1200.00",
                "trend": None,
                "direction": None,
            },
            "period_revenue": {
                "value": "500.00",
                "trend": None,
                "direction": None,
            },
            "ytd": {
                "value": "5000.00",
                "trend": None,
                "direction": None,
            },
        }

        serializer = RevenueSummarySerializer(data=data)

        assert serializer.is_valid()

    def test_serializes_complete_summary(self):
        instance = {
            "lifetime": {
                "value": Decimal("5000.00"),
                "trend": None,
                "direction": None,
            },
            "period_revenue": {
                "value": Decimal("1200.50"),
                "trend": 20,
                "direction": "up",
            },
            "ytd": {
                "value": Decimal("8500.75"),
                "trend": 10,
                "direction": "up",
            },
        }

        serializer = RevenueSummarySerializer(instance=instance)

        assert serializer.data == {
            "lifetime": {
                "value": "5000.00",
                "trend": None,
                "direction": None,
            },
            "period_revenue": {
                "value": "1200.50",
                "trend": 20,
                "direction": "up",
            },
            "ytd": {
                "value": "8500.75",
                "trend": 10,
                "direction": "up",
            },
        }


class TestCourseBreakdownSerializer:
    def test_declares_expected_fields(self):
        serializer = CourseBreakdownSerializer()

        assert set(serializer.fields) == {
            "course",
            "amount",
        }

    def test_course_is_char_field(self):
        serializer = CourseBreakdownSerializer()

        assert isinstance(
            serializer.fields["course"],
            serializers.CharField,
        )
        assert serializer.fields["course"].required is True
        assert serializer.fields["course"].allow_null is False

    def test_amount_is_decimal_field(self):
        serializer = CourseBreakdownSerializer()

        field = serializer.fields["amount"]

        assert isinstance(field, serializers.DecimalField)
        assert field.max_digits == 14
        assert field.decimal_places == 2

    def test_valid_data_is_accepted(self):
        serializer = CourseBreakdownSerializer(
            data={
                "course": "Django Fundamentals",
                "amount": "1250.50",
            }
        )

        assert serializer.is_valid()

        assert serializer.validated_data == {
            "course": "Django Fundamentals",
            "amount": Decimal("1250.50"),
        }

    def test_accepts_zero_amount(self):
        serializer = CourseBreakdownSerializer(
            data={
                "course": "Free Course",
                "amount": "0.00",
            }
        )

        assert serializer.is_valid()
        assert serializer.validated_data["amount"] == Decimal("0.00")

    def test_accepts_negative_amount_at_serializer_level(self):
        serializer = CourseBreakdownSerializer(
            data={
                "course": "Refunded Course",
                "amount": "-100.00",
            }
        )

        assert serializer.is_valid()

        assert serializer.validated_data["amount"] == Decimal("-100.00")

    def test_course_is_required(self):
        serializer = CourseBreakdownSerializer(
            data={
                "amount": "100.00",
            }
        )

        assert not serializer.is_valid()
        assert "course" in serializer.errors

    def test_amount_is_required(self):
        serializer = CourseBreakdownSerializer(
            data={
                "course": "Django",
            }
        )

        assert not serializer.is_valid()
        assert "amount" in serializer.errors

    def test_course_does_not_allow_null(self):
        serializer = CourseBreakdownSerializer(
            data={
                "course": None,
                "amount": "100.00",
            }
        )

        assert not serializer.is_valid()
        assert "course" in serializer.errors

    def test_amount_does_not_allow_null(self):
        serializer = CourseBreakdownSerializer(
            data={
                "course": "Django",
                "amount": None,
            }
        )

        assert not serializer.is_valid()
        assert "amount" in serializer.errors

    def test_rejects_invalid_amount(self):
        serializer = CourseBreakdownSerializer(
            data={
                "course": "Django",
                "amount": "invalid",
            }
        )

        assert not serializer.is_valid()
        assert "amount" in serializer.errors

    def test_rejects_more_than_two_decimal_places(self):
        serializer = CourseBreakdownSerializer(
            data={
                "course": "Django",
                "amount": "100.123",
            }
        )

        assert not serializer.is_valid()
        assert "amount" in serializer.errors

    def test_accepts_maximum_decimal_capacity(self):
        serializer = CourseBreakdownSerializer(
            data={
                "course": "Django",
                "amount": "999999999999.99",
            }
        )

        assert serializer.is_valid()

        assert serializer.validated_data["amount"] == Decimal("999999999999.99")

    def test_rejects_amount_exceeding_max_digits(self):
        serializer = CourseBreakdownSerializer(
            data={
                "course": "Django",
                "amount": "1000000000000.00",
            }
        )

        assert not serializer.is_valid()
        assert "amount" in serializer.errors

    def test_serializes_valid_instance(self):
        serializer = CourseBreakdownSerializer(
            instance={
                "course": "Django Fundamentals",
                "amount": Decimal("1250.50"),
            }
        )

        assert serializer.data == {
            "course": "Django Fundamentals",
            "amount": "1250.50",
        }

    def test_serializes_zero_amount(self):
        serializer = CourseBreakdownSerializer(
            instance={
                "course": "Free Course",
                "amount": Decimal("0.00"),
            }
        )

        assert serializer.data == {
            "course": "Free Course",
            "amount": "0.00",
        }


class TestRevenueSerializer:
    def test_declares_expected_fields(self):
        serializer = RevenueSerializer()

        assert set(serializer.fields) == {
            "revenue_summary",
            "course_breakdown",
        }

    def test_revenue_summary_is_nested_serializer(self):
        serializer = RevenueSerializer()

        field = serializer.fields["revenue_summary"]

        assert isinstance(field, RevenueSummarySerializer)
        assert field.required is True

    def test_course_breakdown_is_nested_many_serializer(self):
        serializer = RevenueSerializer()

        field = serializer.fields["course_breakdown"]

        assert isinstance(field, serializers.ListSerializer)
        assert isinstance(
            field.child,
            CourseBreakdownSerializer,
        )
        assert field.required is True

    def test_valid_complete_data_is_accepted(self):
        data = {
            "revenue_summary": {
                "lifetime": {
                    "value": "10000.00",
                    "trend": None,
                    "direction": None,
                },
                "period_revenue": {
                    "value": "2500.50",
                    "trend": 25,
                    "direction": "up",
                },
                "ytd": {
                    "value": "7500.00",
                    "trend": 15,
                    "direction": "up",
                },
            },
            "course_breakdown": [
                {
                    "course": "Django Fundamentals",
                    "amount": "1500.00",
                },
                {
                    "course": "DRF Advanced",
                    "amount": "1000.50",
                },
            ],
        }

        serializer = RevenueSerializer(data=data)

        assert serializer.is_valid()

        assert serializer.validated_data["revenue_summary"]["period_revenue"][
            "value"
        ] == Decimal("2500.50")

        assert serializer.validated_data["course_breakdown"] == [
            {
                "course": "Django Fundamentals",
                "amount": Decimal("1500.00"),
            },
            {
                "course": "DRF Advanced",
                "amount": Decimal("1000.50"),
            },
        ]

    def test_empty_course_breakdown_is_accepted(self):
        data = {
            "revenue_summary": {
                "lifetime": {
                    "value": "10000.00",
                    "trend": None,
                    "direction": None,
                },
                "period_revenue": {
                    "value": "0.00",
                    "trend": 0,
                    "direction": "neutral",
                },
                "ytd": {
                    "value": "5000.00",
                    "trend": 10,
                    "direction": "up",
                },
            },
            "course_breakdown": [],
        }

        serializer = RevenueSerializer(data=data)

        assert serializer.is_valid()
        assert serializer.validated_data["course_breakdown"] == []

    def test_revenue_summary_is_required(self):
        serializer = RevenueSerializer(
            data={
                "course_breakdown": [],
            }
        )

        assert not serializer.is_valid()
        assert "revenue_summary" in serializer.errors

    def test_course_breakdown_is_required(self):
        serializer = RevenueSerializer(
            data={
                "revenue_summary": {
                    "lifetime": {
                        "value": "1000.00",
                        "trend": 10,
                        "direction": "up",
                    },
                    "period_revenue": {
                        "value": "500.00",
                        "trend": 5,
                        "direction": "up",
                    },
                    "ytd": {
                        "value": "800.00",
                        "trend": 8,
                        "direction": "up",
                    },
                },
            }
        )

        assert not serializer.is_valid()
        assert "course_breakdown" in serializer.errors

    def test_rejects_invalid_summary(self):
        serializer = RevenueSerializer(
            data={
                "revenue_summary": {
                    "lifetime": {
                        "value": "invalid",
                        "trend": 10,
                        "direction": "up",
                    },
                    "period_revenue": {
                        "value": "500.00",
                        "trend": 5,
                        "direction": "up",
                    },
                    "ytd": {
                        "value": "800.00",
                        "trend": 8,
                        "direction": "up",
                    },
                },
                "course_breakdown": [],
            }
        )

        assert not serializer.is_valid()
        assert "revenue_summary" in serializer.errors
        assert "lifetime" in serializer.errors["revenue_summary"]

    def test_rejects_invalid_course_breakdown_item(self):
        serializer = RevenueSerializer(
            data={
                "revenue_summary": {
                    "lifetime": {
                        "value": "1000.00",
                        "trend": 10,
                        "direction": "up",
                    },
                    "period_revenue": {
                        "value": "500.00",
                        "trend": 5,
                        "direction": "up",
                    },
                    "ytd": {
                        "value": "800.00",
                        "trend": 8,
                        "direction": "up",
                    },
                },
                "course_breakdown": [
                    {
                        "course": "Django",
                        "amount": "invalid",
                    }
                ],
            }
        )

        assert not serializer.is_valid()
        assert "course_breakdown" in serializer.errors

    def test_rejects_invalid_item_inside_multiple_breakdown_items(self):
        serializer = RevenueSerializer(
            data={
                "revenue_summary": {
                    "lifetime": {
                        "value": "1000.00",
                        "trend": 10,
                        "direction": "up",
                    },
                    "period_revenue": {
                        "value": "500.00",
                        "trend": 5,
                        "direction": "up",
                    },
                    "ytd": {
                        "value": "800.00",
                        "trend": 8,
                        "direction": "up",
                    },
                },
                "course_breakdown": [
                    {
                        "course": "Django",
                        "amount": "100.00",
                    },
                    {
                        "course": "DRF",
                        "amount": "invalid",
                    },
                ],
            }
        )

        assert not serializer.is_valid()
        assert "course_breakdown" in serializer.errors
        assert serializer.errors["course_breakdown"][1]["amount"]

    def test_serializes_complete_revenue(self):
        instance = {
            "revenue_summary": {
                "lifetime": {
                    "value": Decimal("10000.00"),
                    "trend": None,
                    "direction": None,
                },
                "period_revenue": {
                    "value": Decimal("2500.50"),
                    "trend": 25,
                    "direction": "up",
                },
                "ytd": {
                    "value": Decimal("7500.00"),
                    "trend": 15,
                    "direction": "up",
                },
            },
            "course_breakdown": [
                {
                    "course": "Django Fundamentals",
                    "amount": Decimal("1500.00"),
                },
                {
                    "course": "DRF Advanced",
                    "amount": Decimal("1000.50"),
                },
            ],
        }

        serializer = RevenueSerializer(instance=instance)

        assert serializer.data == {
            "revenue_summary": {
                "lifetime": {
                    "value": "10000.00",
                    "trend": None,
                    "direction": None,
                },
                "period_revenue": {
                    "value": "2500.50",
                    "trend": 25,
                    "direction": "up",
                },
                "ytd": {
                    "value": "7500.00",
                    "trend": 15,
                    "direction": "up",
                },
            },
            "course_breakdown": [
                {
                    "course": "Django Fundamentals",
                    "amount": "1500.00",
                },
                {
                    "course": "DRF Advanced",
                    "amount": "1000.50",
                },
            ],
        }

    def test_serializes_empty_course_breakdown(self):
        instance = {
            "revenue_summary": {
                "lifetime": {
                    "value": Decimal("10000.00"),
                    "trend": None,
                    "direction": None,
                },
                "period_revenue": {
                    "value": Decimal("0.00"),
                    "trend": 0,
                    "direction": "neutral",
                },
                "ytd": {
                    "value": Decimal("5000.00"),
                    "trend": 10,
                    "direction": "up",
                },
            },
            "course_breakdown": [],
        }

        serializer = RevenueSerializer(instance=instance)

        assert serializer.data["course_breakdown"] == []

    def test_supports_nullable_trend_and_direction_throughout_summary(
        self,
    ):
        instance = {
            "revenue_summary": {
                "lifetime": {
                    "value": Decimal("1000.00"),
                    "trend": None,
                    "direction": None,
                },
                "period_revenue": {
                    "value": Decimal("500.00"),
                    "trend": None,
                    "direction": None,
                },
                "ytd": {
                    "value": Decimal("2000.00"),
                    "trend": None,
                    "direction": None,
                },
            },
            "course_breakdown": [],
        }

        serializer = RevenueSerializer(instance=instance)

        assert serializer.data["revenue_summary"] == {
            "lifetime": {
                "value": "1000.00",
                "trend": None,
                "direction": None,
            },
            "period_revenue": {
                "value": "500.00",
                "trend": None,
                "direction": None,
            },
            "ytd": {
                "value": "2000.00",
                "trend": None,
                "direction": None,
            },
        }

    def test_preserves_course_breakdown_order(self):
        data = {
            "revenue_summary": {
                "lifetime": {
                    "value": "3000.00",
                    "trend": None,
                    "direction": None,
                },
                "period_revenue": {
                    "value": "1000.00",
                    "trend": 10,
                    "direction": "up",
                },
                "ytd": {
                    "value": "2000.00",
                    "trend": 20,
                    "direction": "up",
                },
            },
            "course_breakdown": [
                {
                    "course": "Course C",
                    "amount": "300.00",
                },
                {
                    "course": "Course A",
                    "amount": "100.00",
                },
                {
                    "course": "Course B",
                    "amount": "200.00",
                },
            ],
        }

        serializer = RevenueSerializer(data=data)

        assert serializer.is_valid()

        assert serializer.validated_data["course_breakdown"] == [
            {
                "course": "Course C",
                "amount": Decimal("300.00"),
            },
            {
                "course": "Course A",
                "amount": Decimal("100.00"),
            },
            {
                "course": "Course B",
                "amount": Decimal("200.00"),
            },
        ]
