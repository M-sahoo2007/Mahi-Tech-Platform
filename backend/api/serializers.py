from rest_framework import serializers


class DashboardUserSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=("admin", "team"))


class TeamAccountSummarySerializer(serializers.Serializer):
    total = serializers.IntegerField(min_value=0)
    active = serializers.IntegerField(min_value=0)


class DashboardSystemStatusSerializer(serializers.Serializer):
    api = serializers.ChoiceField(choices=("connected",))
    cache = serializers.ChoiceField(choices=("connected", "unavailable"))
    cache_backend = serializers.ChoiceField(choices=("redis", "local"))


class DashboardSummarySerializer(serializers.Serializer):
    current_user = DashboardUserSerializer()
    team_accounts = TeamAccountSummarySerializer()
    system = DashboardSystemStatusSerializer()