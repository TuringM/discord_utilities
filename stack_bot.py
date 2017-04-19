import discord
from discord.ext import commands
import asyncio

description = '''Beep boop.'''
bot = commands.Bot(command_prefix='?', description=description)

@bot.event
@asyncio.coroutine
def on_ready():
    global server_data
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    #yield from bot.say('Beep boop.')

@bot.group(pass_context=True, invoke_without_command=True)
@asyncio.coroutine
def stack(context, command=None):
    global bot
    global help_message
    """Execute a Stack-related command."""
    if command is None:
        yield from bot.say(help_message)
    else:
        yield from bot.say('Invalid stack command.')

@stack.command(pass_context=True)
@asyncio.coroutine
def regchannel(context, channel: str=None):
    """"""
    global bot
    global server_data
    server = context.message.channel.server
    target_channel = None
    for server_channel in context.message.channel.server.channels:
        if server_channel.mention == channel or server_channel.name == channel or server_channel.id == channel:
            if context.message.author.permissions_in(server_channel).administrator:
                target_channel = server_channel
                break
    if target_channel != None:
        server_data[server]['stack_channel'] = target_channel
        yield from bot.say('Registered channel ' + server_data[server]['stack_channel'].mention + ' as stack channel.')
    else:
        yield from bot.say('Error, no channel was registered.')

from copy import deepcopy

@stack.command(pass_context=True)
@asyncio.coroutine
def lock(context):
    """"""
    global bot
    global server_data
    server = context.message.channel.server
    if not context.message.author.permissions_in(context.message.channel.server.default_channel).administrator:
        yield from bot.say('You must be an admin to use this command.')
    elif len(server_data[server]['stored_overwrites']) > 0:
        yield from bot.say('The channel is already locked.')
    elif server_data[server]['stack_channel'] == None:
        yield from bot.say('A channel must be registered first.')
    elif server_data[server]['stack_role'] == None:
        yield from bot.say('A role must be registered first.')
    else:
        for target, overwrite in server_data[server]['stack_channel'].overwrites:
            server_data[server]['stored_overwrites'].append((target, deepcopy(overwrite)))
            overwrite.send_messages = False
            yield from bot.edit_channel_permissions(server_data[server]['stack_channel'], target, overwrite)
        overwrite = discord.PermissionOverwrite()
        overwrite.send_messages = True
        yield from bot.edit_channel_permissions(server_data[server]['stack_channel'], server_data[server]['stack_role'], overwrite)
        yield from bot.say('Channel locked.')

@stack.command(pass_context=True)
@asyncio.coroutine
def unlock(context):
    """"""
    global bot
    global server_data
    server = context.message.channel.server
    if not context.message.author.permissions_in(context.message.channel.server.default_channel).administrator:
        yield from bot.say('You must be an admin to use this command.')
    elif server_data[server]['stack_channel'] == None:
        yield from bot.say('A channel must be registered first.')
    elif server_data[server]['stack_role'] == None:
        yield from bot.say('A role must be registered first.')
    else:
        for target, overwrite in server_data[server]['stored_overwrites']:
            yield from bot.edit_channel_permissions(server_data[server]['stack_channel'], target, overwrite)
        server_data[server]['stored_overwrites'].clear()
        yield from bot.delete_channel_permissions(server_data[server]['stack_channel'], server_data[server]['stack_role'])
        yield from bot.say('Channel unlocked.')

# TODO check that the bot has the perms to assign the permission
@stack.command(pass_context=True)
@asyncio.coroutine
def regrole(context, role: str=None):
    """"""
    global bot
    global server_data
    server = context.message.channel.server
    target_role = None
    if server_data[server]['stack_channel'] == None:
        yield from bot.say('A channel must be registered first.')
    else:
        for server_role in context.message.channel.server.roles:
            if server_role.mention == role or server_role.name == role or server_role.id == role:
                if context.message.author.permissions_in(context.message.channel.server.default_channel).administrator:
                    target_role = server_role
                    break
        if target_role != None:
            if True:
                server_data[server]['stack_role'] = target_role
                yield from bot.say('Registered role ' + server_data[server]['stack_role'].name + ' as stack role for ' + server_data[server]['stack_channel'].mention + '.')
            else:
                yield from bot.say('Could not register role ' + target_role.name + ', as I do not have the permissions to apply it.')
        else:
            yield from bot.say('Error, no role was found with the given name/id.')

@stack.command(pass_context=True)
@asyncio.coroutine
def join(context):
    """"""
    global bot
    global server_data
    server = context.message.channel.server
    if context.message.author.permissions_in(server_data[server]['stack_channel']).read_messages:
        if context.message.author not in server_data[server]['queue_members']:
            server_data[server]['speaking_queue'].append(context.message.author)
            server_data[server]['queue_members'].add(context.message.author)
            if len(server_data[server]['speaking_queue']) == 1:
                yield from bot.add_roles(server_data[server]['speaking_queue'][0], server_data[server]['stack_role'])
                yield from bot.send_message(server_data[server]['stack_channel'], server_data[server]['speaking_queue'][0].mention + ', it is your turn to speak.')
            else:
                yield from bot.say('You have been placed on the queue.')
        else:
            yield from bot.say('You are already on the queue.')
    else:
        yield from bot.say('You do not have read permissions in the appropriate channel to join the stack.')

@stack.command(pass_context=True)
@asyncio.coroutine
def leave(context):
    global bot
    global server_data
    server = context.message.channel.server
    if context.message.author in server_data[server]['queue_members']:
        index = server_data[server]['speaking_queue'].index(context.message.author)
        server_data[server]['speaking_queue'].pop(index)
        server_data[server]['queue_members'].remove(context.message.author)
        yield from bot.say('You have been removed from the stack.')
        if index == 0:
            yield from bot.remove_roles(context.message.author, server_data[server]['stack_role'])
            if len(server_data[server]['speaking_queue']) > 0:
                yield from bot.send_message(server_data[server]['stack_channel'], server_data[server]['speaking_queue'][0].mention + ', it is your turn to speak.')
            else:
                yield from bot.send_message(server_data[server]['stack_channel'], 'The speaking queue is empty. Please use the join command to place yourself on the queue.')
    else:
        yield from bot.say('You cannot leave the stack because you are not in it.')

@stack.command(pass_context=True)
@asyncio.coroutine
def next(context):
    """"""
    global bot
    global server_data
    server = context.message.channel.server
    if context.message.channel == server_data[server]['stack_channel']:
        if len(server_data[server]['speaking_queue']) != 0 and (context.message.author.permissions_in(context.message.channel.server.default_channel).administrator or context.message.author == server_data[server]['speaking_queue'][0]):
            yield from bot.remove_roles(server_data[server]['speaking_queue'][0], server_data[server]['stack_role'])
            queue_member = server_data[server]['speaking_queue'].pop(0)
            server_data[server]['queue_members'].remove(queue_member)
            if len(server_data[server]['speaking_queue']) > 0:
                yield from bot.add_roles(server_data[server]['speaking_queue'][0], server_data[server]['stack_role'])
                yield from bot.send_message(server_data[server]['stack_channel'], server_data[server]['speaking_queue'][0].mention + ', it is your turn to speak.')
            else:
                yield from bot.say('The speaking queue is empty. Please use the join command to place yourself on the queue.')
        elif len(server_data[server]['speaking_queue']) == 0:
            yield from bot.say('The speaking queue is empty. Please use the join command to place yourself on the queue.')
        else:
            yield from bot.say('You do not have the permissions necessary to move to the next speaker.')
    else:
        pass # Ignore the message.

from collections import defaultdict

def default():
    return {'stack_channel': None, 'stack_role': None, 'speaking_queue': [], 'queue_members': set(), 'stored_overwrites': []}

help_message = """```
?stack regchannel [channel-name]: registers the stack channel.
?stack regrole [role-name]: registers the role channel.
?stack join: puts the author of the message on the stack, if they are not already.
?stack leave: takes the author out of the stack, if they are on it.
?stack next: only recognized in the stack channel itself. Used by the current speaker or admins (when appropriate), removes the current speaker from the stack and lets the next person speak.
```"""
from pickle import load, dump
from pathlib import Path
save_location = Path('server_data.pickle')
try:
    with save_location.open('rb') as save_fp:
        server_data = load(save_fp)
except FileNotFoundError:
    server_data = defaultdict(default)
try:
    with open('turing-machine-token.dat') as token_fp:
        bot.run(token_fp.read().strip())
except FileNotFoundError:
    print('No token file was found.')
finally:
    try:
        for server in server_data:
            server_data[server]['speaking_queue'].clear()
            server_data[server]['queue_members'].clear()
        with save_location.open('wb') as save_fp:
            dump(server_data, save_fp)
    except:
        print('Failed to save data.')
        raise
