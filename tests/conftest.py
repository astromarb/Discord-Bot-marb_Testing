"""Shared pytest fixtures and configuration for BornAgain bot tests."""

import pytest
from unittest.mock import MagicMock, AsyncMock
import discord
from cachetools import TTLCache

from Bot import Bot
from client.supabase_client import SupabaseClient
from client.rift_watcher_client import RiftWatcherClient
from helper.guild_configuration_manager_helper import GuildConfigurationManagerHelper


@pytest.fixture
def mock_discord_interaction():
    mock = MagicMock(spec=discord.Interaction)
    mock.guild_id = 123456
    mock.user = MagicMock(spec=discord.User)
    mock.user.id = 789012
    mock.user.name = "TestUser"
    mock.channel = MagicMock(spec=discord.TextChannel)
    mock.channel.id = 999888
    mock.response = MagicMock()
    mock.response.send_message = AsyncMock()
    return mock


@pytest.fixture
def mock_discord_member():
    mock = MagicMock(spec=discord.Member)
    mock.id = 789012
    mock.name = "TestMember"
    mock.mention = "@TestMember"
    mock.guild = MagicMock(spec=discord.Guild)
    mock.guild.id = 123456
    mock.guild.name = "TestGuild"
    mock.guild.members = [MagicMock() for _ in range(5)]
    mock.guild.roles = [
        MagicMock(spec=discord.Role, name="Member"),
        MagicMock(spec=discord.Role, name="Moderator"),
    ]
    mock.guild.system_channel = MagicMock(spec=discord.TextChannel)
    mock.guild.system_channel.id = 555666
    mock.add_roles = AsyncMock()
    return mock


@pytest.fixture
def mock_discord_guild():
    mock = MagicMock(spec=discord.Guild)
    mock.id = 123456
    mock.name = "TestGuild"
    mock.member_count = 50
    mock.channels = [MagicMock() for _ in range(10)]
    mock.roles = [
        MagicMock(spec=discord.Role, name="Member"),
        MagicMock(spec=discord.Role, name="Admin"),
    ]
    return mock


@pytest.fixture
def mock_discord_text_channel():
    mock = MagicMock(spec=discord.TextChannel)
    mock.id = 999888
    mock.name = "announcements"
    mock.guild = MagicMock(spec=discord.Guild)
    mock.guild.id = 123456
    mock.send = AsyncMock()
    return mock


@pytest.fixture
def mock_supabase_client(mocker):
    mock = MagicMock(spec=SupabaseClient)
    mock.get_server_data.return_value = MagicMock(
        data=[{
            "guild_id": 123456,
            "default_role": "Member",
            "rules": ["No spam", "Be respectful", "Follow Discord TOS"],
            "channels": {
                "announcement_channel_id": 999888,
                "welcome_channel_id": 111222,
                "rules_channel_id": 333444,
            },
            "image_urls": {
                "welcome_image_urls": ["https://example.com/welcome1.png", "https://example.com/welcome2.png"],
                "announcement_image_urls": ["https://example.com/announce1.png", "https://example.com/announce2.png"],
            }
        }]
    )
    return mock


@pytest.fixture
def mock_rift_watcher_client(mocker):
    mock = MagicMock(spec=RiftWatcherClient)
    mock.get_player_overview = AsyncMock(return_value={
        "puuid": "test-puuid-12345",
        "display_name": "TestPlayer",
        "region": "NA1",
        "rank": "47 LP",
        "ranked_tier": "Diamond",
        "ranked_division": "II",
        "flex_rank": "Gold",
        "flex_ranked_division": "IV"
    })
    return mock


@pytest.fixture
def guild_config_manager(mocker, mock_supabase_client):
    manager = GuildConfigurationManagerHelper()
    mocker.patch.object(manager, 'supabase_client', mock_supabase_client)
    manager.cache.clear()
    return manager


@pytest.fixture
def bot_instance(mocker, mock_supabase_client, mock_rift_watcher_client):
    mocker.patch.object(Bot, 'create_client', return_value=MagicMock())
    bot = Bot()
    bot.guild_configuration_manager_helper.supabase_client = mock_supabase_client
    bot.rift_watcher_client = mock_rift_watcher_client
    return bot


@pytest.fixture
def valid_guild_config():
    return {
        "guild_id": 123456,
        "default_role": "Member",
        "rules": ["No spam", "Be respectful", "Follow Discord TOS"],
        "channels": {
            "announcement_channel_id": 999888,
            "welcome_channel_id": 111222,
            "rules_channel_id": 333444,
        },
        "image_urls": {
            "welcome_image_urls": ["https://example.com/welcome1.png"],
            "announcement_image_urls": ["https://example.com/announce1.png"],
        }
    }


@pytest.fixture
def valid_player_data():
    return {
        "puuid": "test-puuid-12345",
        "display_name": "TestPlayer",
        "region": "NA1",
        "rank": "47 LP",
        "ranked_tier": "Diamond",
        "ranked_division": "II",
        "flex_rank": "Gold",
        "flex_ranked_division": "IV"
    }


@pytest.fixture
def unranked_player_data():
    return {
        "puuid": "test-puuid-67890",
        "display_name": "NewPlayer",
        "region": "NA1",
        "rank": None,
        "ranked_tier": None,
        "ranked_division": None,
        "flex_rank": None,
        "flex_ranked_division": None
    }


@pytest.fixture
def ttl_cache():
    return TTLCache(maxsize=128, ttl=43200)


@pytest.fixture(autouse=True)
def reset_cache(ttl_cache):
    ttl_cache.clear()
    yield
    ttl_cache.clear()


def pytest_configure(config):
    config.addinivalue_line("markers", "asyncio: mark test as async")
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
