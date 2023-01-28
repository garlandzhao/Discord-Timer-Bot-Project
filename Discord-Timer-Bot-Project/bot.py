#This project focuses on creating a personal timer bot
import discord
from discord.ext import commands
import asyncio
from datetime import datetime
import pytz
import re
import math

#Must enable intents on the discord bot page
intents = discord.Intents.all()
intents.members = True

client = discord.Client(intents = intents)

#Replace bot_token with your own token
bot_token = "INSERT BOT TOKEN HERE"

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

bot = commands.Bot(command_prefix='$', intents = intents) #command decorator

#Command to show all commands
@bot.command(pass_context=True)
async def timerhelp(ctx):
    embed_commands_message = discord.Embed(
        title = "Command List",
        description = "\n**$cancel** (timer_name) - cancels an ongoing timer" +
        "\n**$timer** (time, message) - Set a timer with an option to include a reminder message" +
        "\n**$timerhelp** - Displays a list of available commands" +
        "\n**$timerlist** - Displays a list of avalible timers" +
        "\n**$today **(time_zone) - Displays the current date and time",
        color = discord.Colour.blue()
        )
    await ctx.send(embed = embed_commands_message)

#Command to show the current date and time
@bot.command(pass_context=True)
async def today(ctx, time_zone = "US/Pacific"):
    try:
        #get current time and date
        time_zone = pytz.timezone(time_zone)
        current_datetime = datetime.now(time_zone)

        #convert current time and date into easier to read formats
        today_date = current_datetime.strftime("%b %d, %Y")
        current_time = current_datetime.strftime("%I:%M %p")
        day_name = current_datetime.strftime("%A")

        embed_datetime_message = discord.Embed(
                title = "Today: ",
                color = discord.Colour.blue()
                )
        embed_datetime_message.add_field(
                name = "Date",
                value = today_date + " (" + day_name + ")"
                )

        embed_datetime_message.add_field(
                name = "Time",
                value = current_time + " " + str(time_zone), 
                inline = False
                )
        await ctx.send(embed = embed_datetime_message)

    except:
        embed_today_error_message = discord.Embed(
            title = "Error",
            color = discord.Colour.red()
            )
        embed_today_error_message.add_field(
            name = "Incorrect Timezone",
            value = "A list of timezones can be found [here](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) under TZ database names",
            )
        await ctx.send(embed = embed_today_error_message)

#Variable used to hold timers
timer_tasks = set()

#Command to view active timers 
@bot.command(pass_context=True)     
async def timerlist(ctx):
    active_tasks = timer_tasks
    active_tasks_list = []

    #remove completed tasks and add to an active tasks list
    if len(timer_tasks) > 0:
        for task in active_tasks:
            task.add_done_callback(active_tasks.discard)
            active_tasks_list.append(task.get_name())
        
        active_tasks_list = "\n".join(active_tasks_list)
        embed_active_timers_message = discord.Embed(
            title = "Timers List",
            description = active_tasks_list,
            color = discord.Colour.blue()
            )

        await ctx.send(embed = embed_active_timers_message)

    else:
        embed_active_timers_error_message = discord.Embed(
            title = "Error",
            description = "There are no active timers running",
            color = discord.Colour.red()
            )
        await ctx.send(embed = embed_active_timers_error_message)

#Command to cancel ongoing timer
@bot.command(pass_context=True)     
async def cancel(ctx, task_name = "   "):
    try:
        if len(timer_tasks) > 0:
            for task in timer_tasks:
                if task_name == task.get_name():
                    task.cancel()
                    #remove timer from list of timers
                    task.add_done_callback(timer_tasks.discard)
                    embed_cancel_confirm_message = discord.Embed(
                        title = "Timer Cancelled",
                        description = task.get_name() + " is cancelled by " + ctx.message.author.display_name,
                        color = discord.Colour.blue()
                        )
                    return await ctx.send(embed = embed_cancel_confirm_message)
        raise Exception("Error")
    except:
        embed_cancel_error_message = discord.Embed(
            title = "Error",
            description = "There are no timers named: " + task_name + "\nPlease refer to **$timerlist**",
            color = discord.Colour.red()
            )
        await ctx.send(embed = embed_cancel_error_message)

#Command to set a timer
@bot.command(pass_context=True)
async def timer(ctx, set_time, *, reminder_message = None):
    #seperate userinput into time and time unit
    try:
        if re.search("[a-zA-z]",set_time) is not None:
            if (".") in set_time:
                time_unit = re.split(r"(\d+)",set_time)[4]
                set_time = re.split(r"[a-zA-Z]+",set_time)[0]
            else:
                temp_set_time = re.split(r"(\d+)",set_time)
                set_time = temp_set_time[1]
                time_unit = temp_set_time[2]
        set_time = float(set_time)

        #some restrictions
        if (set_time < 0.0) or (set_time > 1000.0):
            raise Exception("Error")
        time_unit = time_unit.lower()

        #remove the ending "s"
        if len(time_unit) > 1:
            if time_unit[-1] == "s":
                time_unit = time_unit[:-1]

        #convert input into seconds
        if (time_unit == "h" ) or (time_unit == "hr" ):
           time_in_seconds = set_time * 3600.0

        elif (time_unit == "m" ) or (time_unit == "min" ):
            time_in_seconds = set_time * 60.0

        elif (time_unit == "s" ) or (time_unit == "sec" ):
            time_in_seconds = set_time
        else:
            raise Exception("Error")

        time_in_seconds = int(math.floor(time_in_seconds))

        #Create function to display the timer
        async def display_timer():
            try:
                #send a placeholder countdown notification
                embed_countdown_message = discord.Embed(
                    title = "Timer",
                    description = "Time Remaining: ```XX:XX:XX```",
                    color = discord.Colour.blue()
                    )

                countdown = await ctx.send(embed = embed_countdown_message)

                #Initalize variables
                temp_hour = -1
                temp_min = -1
                task_name = task.get_name()
                for i in reversed(range(time_in_seconds)):
                    min, sec = divmod(i , 60)
                    hour, min = divmod(min, 60)
   
                    await asyncio.sleep(1)
                    if (temp_hour != hour) or (temp_min !=min):
                        if (hour > 0) or (min > 0):
                            new_embed_countdown_message = discord.Embed(
                                title = "Time Remaining:",
                                description = "```{:02d}:{:02d}:XX``` \n To cancel type: $cancel {}".format(hour,min,task_name),
                                color = discord.Colour.blue()
                                )

                            await countdown.edit(embed = new_embed_countdown_message)
                        else:
                            new_embed_countdown_message = discord.Embed(
                                title = "Timer",
                                description = "Time Remaining: ```<1 min```",
                                color = discord.Colour.blue()
                                )
                            await countdown.edit(embed = new_embed_countdown_message)

                    temp_hour = hour
                    temp_min = min
                    
                #have different messages for timers and reminders
                if (reminder_message is None):
                    completion_message = "Your alarm for " + str(set_time) + " " + time_unit + " is complete"
                    embed_completion_message = discord.Embed(
                            title = "Alert Message",
                            description = completion_message,
                            color = discord.Colour.blue()
                            )
                    await ctx.send(embed = embed_completion_message)

                else:
                    embed_reminder_message = discord.Embed(
                            title = "Reminder",
                            description = reminder_message,
                            color = discord.Colour.blue()
                            )
                    await ctx.send(embed = embed_reminder_message)
                await countdown.delete()

            except:
                await countdown.delete()

        #create the timer task
        coro = display_timer()
        task = asyncio.create_task(coro)

        #add task to a set
        count = len(timer_tasks) + 1
        task.set_name("timer" + str(count))
        timer_tasks.add(task)

    except:
        embed_error_message = discord.Embed(
                title = "Format Error",
                description = "**$timer (desired time, time measurement, message)**" + 
                "\nDesired time must be between 0 and 1000" +
                "\nEx. **$timer 5s** or **$timer 5s message**",
                color = discord.Colour.red()
                )

        return await ctx.send(embed = embed_error_message)

    try: 
        await task
        task.add_done_callback(timer_tasks.discard)
        
    except:
            pass

    finally:
            #ping the caller and delete ping after 5 mins
            await ctx.send(ctx.message.author.mention, delete_after = 300.0,)

bot.run(bot_token)
client.run(bot_token)