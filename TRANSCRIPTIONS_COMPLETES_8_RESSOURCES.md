# DOSSIER COMPLET : TRANSCRIPTIONS INTÉGRALES DES 4 VIDÉOS ET DES 4 TWEETS

Ce document regroupe mot à mot l'intégralité des 8 ressources partagées pour audit critique.

---

# SECTION 1 : LES 4 TWEETS BRUTS (MOT À MOT)

### Tweet 1 : @NicoGarcia_IA (31/10/2026)
Lien : https://x.com/NicoGarcia_IA/status/2116515550549733710
Texte brut :
"""
🔴 ALGUIEN HA FILTRADO ESTE PROMPT PARA CREAR AGENTES DE TRADING

Lo pegas en Claude Code y te monta el bot.
Sin programar.
Detecta si el mercado está tranquilo, lateral o en caída y cambia de estrategia.
Freno de mano: drawdown máximo del 15% y comprueba antes de cada orden.
Prueba la estrategia con datos reales y se niega a operar si no le gana al mercado.
Mientras duermes analiza qué falló y te deja mejoras.
Pegas, rellenas tus datos y Claude hace el resto.
"""

---

### Tweet 2 : @ludoonchart (31/10/2026)
Lien : https://x.com/ludoonchart/status/2116597215342821528
Texte brut :
"""
JPMorgan and Goldman Sachs have trading technology sitting on GitHub for FREE, and most traders have no idea it exists

I'm talking about 3 open-source projects that give you the building blocks of a Wall Street-style quantitative trading workstation:
Market data, advanced financial analytics, portfolio risk management and professional trading dashboards

Here's how you can try them yourself:
step 1 → JPMorgan Perspective
Originally developed at JPMorgan, Perspective is a high-performance framework for visualizing large streams of financial data, with interactive dashboards, streaming analytics, financial charts and heatmaps
GitHub: https://github.com/perspective-dev/perspective

step 2 → Goldman Sachs GS Quant
A quantitative finance toolkit developed by Goldman Sachs quants for financial modeling, derivatives analysis, portfolio risk management and statistical research
GitHub: https://github.com/goldmansachs/gs-quant

step 3 → Fincept Terminal
An open-source financial workstation that combines market monitoring, financial data analysis, portfolio analytics and quantitative research tools in one platform
GitHub: https://github.com/Fincept-Corporation/FinceptTerminal

step 4 → build your own quant workflow
Use Perspective for market visualization, GS Quant for financial analysis and Fincept as a research workstation
Connect supported data sources, develop quantitative strategies, analyze portfolio exposure and explore market opportunities
Some institutional APIs require separate access, but the open-source tools provide a powerful starting point
the result → a customizable quantitative research setup built around technologies from Wall Street and the open-source finance community
3 GitHub repositories
Thousands of developers
Professional financial technology you can explore for free
i'll leave the rest to you…
"""

---

### Tweet 3 : @PaulYoungX (20/10/2026)
Lien : https://x.com/PaulYoungX/status/2112457730522861617
Texte brut :
"""
🚨 QUELQU'UN A FAIT FUITER LE PROMPT POUR CRÉER DES AGENTS DE TRADING. TU LE COLLES DANS CLAUDE CODE ET IL MONTE LE BOT PENDANT QUE TU PRENDS UN CAFÉ

Sans coder. Juste coller. Un seul prompt fait tout :
Temps nécessaire : 1 minute
Action : copier-coller dans Claude Code

L'erreur qui vide le compte de 99% des traders avec des bots : ils utilisent la même stratégie pour tout. Sauf que le marché n'est pas le même un mardi tranquille et en plein crash.

→ Il lit le marché comme un quant : il détecte s'il est calme, latéral, nerveux ou en chute libre, et change de stratégie à chaque fois
→ Frein à main : drawdown maximum de 15% et un bouton d'arrêt vérifié avant CHAQUE ordre
→ Examen avant l'argent : il teste la stratégie période par période avec des données réelles et refuse de trader s'il ne bat pas le marché
→ Équipe de nuit : pendant que tu dors, il analyse ce qui a raté et te laisse des améliorations prêtes. C'est toi qui décides de les appliquer
→ Zéro code : tu colles, tu remplis tes infos et Claude fait le reste

Avant, ça demandait une équipe de docteurs, des milliers de lignes de code et des semaines de travail.
Maintenant, c'est Ctrl+V.
Sauvegarde-le avant qu'on le supprime 🔖
"""

---

### Tweet 4 : @gelorria (31/10/2026)
Lien : https://x.com/gelorria/status/2116510060977561854
Texte brut :
"""
CÓMO CREAR UN BOT DE TRADING CON CLAUDE
Tutorial paso a paso, gratuito y de 23 minutos.
→ Construirlo desde cero
→ Usar Claude como base
→ Órdenes de compra y venta
🔖 Guárdalo.
"""

---

# SECTION 2 : TRANSCRIPTIONS INTÉGRALES DES 4 VIDÉOS YOUTUBE

---

## VIDÉO 1 : Peter Rush
Titre : Full Guide to Building an AI Trading Bot with ChatGPT AI Agents
Lien : https://youtu.be/rN7pXgjnam0
Durée : 6:41
Description originale : References & Sources: https://s3.amazonaws.com/gdpage/index.html

TRANSCRIPTION MOT À MOT INTÉGRALE :
Take a good look at this balance. That's a full 24 hours of profit for my crypto trading bot. And here's the part that matters. I never wrote a single line of its code, and I didn't touch it once while it ran. Keep that number in mind because we're coming back to it at the end. Let me rewind and show you exactly how this thing was built. Here's how it earns. Decentralized exchanges, Uniswap is a classic example, hold a queue of pending transactions called an order book. The bot watches that order book around the clock. When it spots a big unconfirmed buy, it pays a slightly higher gas fee, so our transaction cuts in front, then drops a sell order right behind it. The price gap between those two fills is the profit, plus a cut of the exchange fees along the way. Simple in concept, impossible to do by hand at that speed. The AI handles every bit of it, which is what makes this one of the easiest ways I've found to make money online. Now, before we build, if this bot is so good, why give it away free? Simple. One, this strategy doesn't divide like a pie. The bot hunts individual pending transactions across the exchanges with enormous daily volume. So, you running it doesn't touch my results. We're fishing in an ocean, not a barrel. Two, this channel is my job. The content the testing and every new user helps me find edge cases faster than I could alone. Three, the code was open source from day one, built on public infrastructure and deployed individually on your own contract. I didn't invent any of it, and gatekeeping it felt wrong. So, no catch, no vault. All right, let's build yours. Grab a Web3 extension if you don't have one. Then head to this site, the platform we use for deploying on Ethereum. All links are in the description. New file, any name. Paste in this code, open source like I said, so audit it however you like. Open this tab in the side menu and hit this button. Connect your extension here. Pick this option. Press connect and your account prints into the console. Click here. Confirm once more, wait for the green light. That's the control panel. Before touching anything, hit this button and check this address matches your extension address. That's cryptographic on-chain proof the contract belongs to you and only you. Now the numbers. 0.5 ETH is the hard minimum. Below that, liquidity problems and gas costs flip profit into losses. So, don't run it underfunded. 1 to 4 ETH is the recommended range. Copy the contract address with this button. Your wallet needs 1 ETH or more, plus a little extra for gas. Then, send, choose ETH, paste the address, enter your amount one or above, and approve. The balance shows up here. Good. Now, start it. Click here, confirm. That's the entire setup. A few hours in, solid numbers so far. Results shift with network traffic and other live conditions, so I'm leaving it completely untouched for a full 24 hours to prove it's stable. Okay, day's done. Final balance. Right back at that number from the start of the video. Every single action the contract took is sitting in the terminal longs, open source, verifiable end-to-end, so your money is never a black box. When you're ready to cash out, this button plus one confirmation brings everything back to your wallet. This video is educational only. I'm not a professional and nothing here is professional advice. Just my own experience. If this one helped, drop a like and hit subscribe. More like this on the way.

---

## VIDÉO 2 : BentoBoi
Titre : I Gave AI ,000 to Trade Crypto
Lien : https://youtu.be/eKs5x77twE0
Durée : 12:22

TRANSCRIPTION MOT À MOT INTÉGRALE :
I'm going to give you AI $10,000 for the next 7 days to see if we can actually make a profit. The internet is filled with AI trading bots claiming they can print you money. However, it got me thinking, can a normal person actually use AI to make money trading crypto? So, I'm starting from scratch building an AI trading bot and I'm going to give it $10,000 of my own money to trade. So, the goal is simple, use AI to outperform the largest crypto token, Bitcoin, and hopefully make some money. If this works, I might have found one of the best ways to print money online or I might just let a chatbot gamble away 10 grand. And there's only one rule, I have to take every trade the AI recommends and document it transparently. Then by the end of the week, how much money we made or lost. I have no idea how to code. But if you've been online recently, you might know the AI models are so good you actually don't need a technical background or coding experience to build out a trading bot. And we're actually able to do this in our last video. So, I started doing some in-depth research and got to brainstorming how we're actually going to make money with AI. I was watching tutorials, writing, thinking, and stumbled upon a genius idea which leads us to our game plan. So, the first thing we're going to do is buy an online trading course from a reputable person. This way we don't actually have to come up with our own trading strategy. Instead, we can take a proven strategy from a trader who's actually better than us and implement it into our system. And this leads us to step two. Once we actually have the course, we're going to give all of the information over to the AI so it knows exactly what to do. This way we're going to feed the AI model with the best information and tools that it can use and it can come up with its own trading strategy based off of the content we give it. Then step number three, we're going to have the AI actually give us some trade alerts and then we can place them and hopefully make some money. And I don't know about you guys, but I think this is a pretty decent idea and I think we might just be able to pull this off. But the only way to find out was executing our plan and seeing what happens. All right, everybody. So, it is currently day two of the challenge and we actually have been working non-stop since the last clip. So, a little bit of an update, we did get the AI installed on our computer and we're going to be using Claude code for this whole entire challenge. And we did go ahead and buy the max plan to build this whole thing out which cost $200. And we did choose this model because this is the best AI out right now. And I do think that this will help a lot during our build process. And on top of that, we did a lot of research and we found the person we do want to track. And this is going to be KillaXBT on X. I have just been personally following him for quite a bit of time, and I really like the content and stuff he puts out. But his course costs $1,000. This person has a huge following, and it also looks like he has a good track record, and he also has good credibility as well. So, I did go ahead and buy the $1,000 course. And hopefully this goes well so we can recoup the $1,200 that we spent so far on this video, but I guess we will have to find out. After we click purchase on the $1,000 course, you do get a massive PDF, and this is over 60 pages long going over his methodology. So, I went ahead and downloaded all of the information, and I fed it to the AI. After a few hours of talking back and forth, it [music] did actually come up with a strategy that we could implement. Okay, so the strategy the AI came up with seems to be very simple. So, in the course material, there was a lot of strategies and indicators that we should look out for. And the course does highlight things that makes a good [music] trade setup. So, the AI found the five best trade indicators that we should be looking out for and committed it to memory. So, using the indicators the AI chose, if multiple of them actually fire off at the same time, AI is actually going to give me a Discord [music] ping or alert to take a trade, and that is exactly what we're going to do. And to make things even more interesting for the challenge, we are actually going to be able to long and short the market. So, for those of you who don't know, if you do long the market, you are expecting it to go up, and you can make money when the market moves in the upward direction. However, if you do short the market, you actually make money when the market goes down. So, by trading this way, you can make money regardless if the money goes up or down. You just have to pick [music] the right direction. And on top of that, we are actually going to be using leverage for this challenge. So, this means we're technically going to be able to take out a loan. So, for this challenge, we're only going to be using 3x leverage. So, instead of the $10,000 original budget, we're technically going to be able to trade with $30,000 in size. [music] So, now we have everything set up, and we just have to wait at our computer for a Discord alert to pop up, and we can take our first trade. Okay, so the first trade is placed. We currently have a $3,500 position on Solana, and we are shorting it. So, we do want the price to go down. And next up, we going to be shorting Doge Coin. So, we have a $1,400 short on Doge Coin. So, we also want the price of this to go down as well. So, shortly after this clip, we actually got two more notifications. One saying to short hype. So, we did go ahead and place a $2,000 position. Then the next notification was to short Bitcoin. So, we did go ahead and place a $2,000 position on this one as well. So, it did seem like the AI was projecting the market to go downwards. So, we shorted the market on four different tokens. So, we really need the market to go down so we can make some money. But, I am happy that the alerts are actually popping up and we do have our first trade. But, we're just going to have to wait and see how these things turn out. I'm super stoked about it though. And who knows? Maybe we'll be millionaires. >> [music] >> Good morning, everybody. So, we did place four trades yesterday and it's time to check and see how they're actually doing. So, we're going to go ahead and take a look at all of the positions right now. >> [screaming] >> All right. So, the update is that we are down. On the Solana trade, we are down $14. On the hype trade, we are down $108. Then on the Bitcoin trade, we are down $26. But, I guess on the bright side, we made $8.79 on Doge. So, that brings us to a total loss of $140.84. Our stop losses also didn't hit. So, I think I'm just going to keep the positions open and see what happens. But, I'm going to go ahead and talk to the AI and see what went wrong and possibly why we're losing all of these trades. Maybe it's just part of the game. So, it does seem like the market actually pumped a lot today. So, it was a bad time to go short for us. But, hey. At least we got $8 on Doge. Let's go. So, I guess for the rest of the day, we're going to try to refine and maybe better the strategy. However, we're still going to be on the lookout for some trades that we could possibly take throughout the day. Okay. So, it is night time now and we do actually have a two more updated trades. So, we do have a Sui short. But, we also got an Ethereum long. So, that's a little bit weird that we're longing and shorting the market. But, I'm going to go ahead and place these trades regardless. So, our current positions haven't changed that much since the morning. So, because we have so many short positions, I'm only going to go in with a $1,000 position shorting Sui, and I'm going to be going in with a $1,500 long on Ethereum. So, hopefully we wake up tomorrow up a good amount of money, but we will see. So, it is not a good morning at all. So, after I woke up today, I checked on the positions and almost all of them were down in the dumps, and within a few hours, basically all of them hit their stop losses. But, the worst part about the whole entire thing is our positions got closed out right before the market actually started to turn to the downside. So, we would have actually probably made money if our positions didn't get closed out, and that is pretty frustrating. Uh I kind of feel like the gold miner meme who was so close to making riches, but the position got closed out right before. But, a wise man once said, "Nothing changes if nothing changes." >> Nothing changes if nothing changes, man. >> So, the trading strategy and bot we set up right now has a very, very low win rate. So, I'm going to make the executive decision to pause the bot and come up with a new strategy. I think I do have to do a lot more research, and I do think it'd be beneficial if I did take a look into the code and actually did more testing with the help of AI. So, I'm going to go ahead and do that now, and hopefully I can figure out what the problem is, or maybe we'll find out that there's no problem at all. Okay, guys. So, we have quite a bit of an update. So, I watched a ton of YouTube videos and talked back and forth with the AI, and I realized that I have been missing quite a bit of information. The first thing that I did actually find out is backtesting, and I have no idea why I didn't think of this to start with. But, basically you can backtest your strategy on the market and see if the strategy is profitable to begin with. This way you can immediately see if it's profitable or not. So, after I learned about backtesting, I set up a bot that can actually do this over and over, and I plugged in our strategy that we're currently using. The win rate for the strategy we're using right now is only 50.6%. So, we are barely winning. But, technically speaking, we did actually code a profitable bot in 2 days, so that is pretty awesome. But, it's not great at all. Another thing that I quickly found out by doing more research is if you are doing short-term trading like we are doing in this video, that is the hardest strategy to pull off, and it is very, very rare that someone is actually able to consistently make gains. This is because in general, if you're trading on a shorter time frame, there's a lot more variance and randomness. And I was also watching a very reputable person on YouTube, and he was saying how he tried over 2,000 strategies and he only uses seven because a lot of these just simply do not work. So, it is definitely possible to make a profitable bot, but it is very, very hard to find. Even though we have all these things stacked up against us, I am not quitting. So, the new game plan is to update our current strategy using our newfound knowledge. Then we're going to plug it into our back tester and see if it's actually profitable. Then lastly, we're going to be making all the money we lost using our new said strategy. Good morning, everyone. It is day five, and we have consumed a lot of caffeine, as you can see here, and I'm feeling pretty good. So, I just want to keep it really real with you guys. I cannot, for the life of me, get a profitable bot running. I tried so many things. I tried editing our current strategy to maybe try to get it to be more profitable. Couldn't do it. I tried finding other strategies online and tried to pay someone, but his group was full, [music] and I couldn't get any of the indicators. I also tried making another one from scratch, and I still could not do it. So, something I'm starting to realize is that coming up with a profitable bot and printing money out of thin air is actually really hard, especially trying to do it in just [music] a week. And on top of this, we are still trading using the old strategy that we did implement, and we are down even more money. So, a lot of you guys might be thinking, "Oh, I'm going to quit on the challenge just because it's too hard." But no, we are going to stick with it. So, as I was scrolling online, I actually found a platform called HyperLiquid, and because we can see everyone's trades, I had the idea to copy some of the top traders on the platform. What I'm planning to do is say track the top 30 wallets and see where all of their positions are overlapping, whether that is long or short, and we can just sneakily place our bet in there, and hopefully we can make some money. you guys are subscribed, you might know we did this in our last video with Polymarket, and it actually turned out to be really good. So, I'm basically just taking the same exact strategy we ran there, but doing it with crypto. And I don't know about you guys, but I think it's a super good idea, especially if we can find the right whales or wallets to track because we're basically taking the smartest and most profitable people in the space, and we're actually just seeing where all of their positions are lying, and we're just going to copy them. I think it's a great idea. So, I actually went ahead and set the whole entire thing up, and the site is fully functional and up and running and it actually gave us our first trade alerts and a lot of the position sizes are also in the tens of millions of dollars as well. So, it does seem like these guys do not play around and I think a lot of these traders are actually using really intelligent algorithms or bots or they have a lot of smart people managing these portfolios. So, on screen here is the full site and you can see if the whales are long on a specific coin or if they're short. And on top of that, you do get their average entry price so you can see how much leverage they're using and you can also see how many whales are in on a specific trade. And my thought process is if there's a lot of whales betting in a specific direction, then there's a high confluence or conviction that the trade will pan out and we should actually take it. And I also set up the bots to give me notifications as well so we can take these trades really fast. So, we're going to see how this works and if we can actually make a profit. So, for the next few days I went on with my life and have my phone on me at all times. I was checking constantly for notifications and when one popped up, I placed the trade immediately using our new and improved strategy. All right, so it is officially day seven and the end of the challenge so it's time to go over the results. And the results were pretty crazy. So, picking up where we left off at our last check-in, we were down $434. But using our new and improved strategy, we actually placed some new trades so we did long a Bitcoin and we actually made $29. And the next trade after that, we did long Ethereum and we actually made $34. So, I was waiting around but I did see that all of the whales were basically shorting the market very very heavily. So, I decided to hop in on this trend and up my size and short the market pretty big. And as some of you may have guessed, the market absolutely ripped in my face. So, as I shorted the market and bet on the price to go down, the market actually went up astronomically. And this move was one of the biggest short liquidations in crypto's history. So, the price did move up a lot and a good amount of the whales lost money and I also did as well. So, we're going to go over the trades. So, the first trade was a short on XRP and we did lose $80. The next trade we took was a short on Bitcoin and we ended up losing $130 on this one. Then we placed a pretty big bet shorting Solana and we did actually lose $342 on this trade. And then lastly, as the time did expire, we did actually lose $9 on a sui short position. So, before we go over the final P&L, I did want to go ahead and say I still do think that AI trading is viable. And I do think you're going to have to take a lot of time learning the skills, the systems, and basically finding the correct strategy. And the odds that you'll make a crypto bot that prints money in just 1 week is just very, very slim, especially if you're starting from zero. So, the grand total loss for the entire week is going to be $953, but if you do include the course and the Cloud subscription, this is going to come out to a $2,153 loss. So, if you do want to see me build out the wealth tracking bot, make sure to follow my second channel. Also, if you guys are interested in growing your personal brand on YouTube and want to work with me one-on-one, make sure to click the first link in the description down below. Also, if you want to see AI trade on Polymarket, make sure to click this video.

---

## VIDÉO 3 : Richard Donchian
Titre : I Built an AI Trading Bot With Claude AI Opus 5.5 - ,9k in 24 Hours (Full Guide)
Lien : https://youtu.be/9y7OxnMsSSw
Durée : 5:54
Description originale : Full Guide Here: https://tr.ee/Z1kCzT

TRANSCRIPTION MOT À MOT INTÉGRALE :
I want to show you something I've been building on the side, a crypto trading bot that runs on AI. This thing has honestly become one of my most consistent sources of passive [music] income. Over the years, I've experimented with plenty of ways to make money online, but nothing has worked quite as well as this AI-powered trading approach. What's really cool about this is that I built the whole system using AI and autonomous [music] agents from the ground up. So, even if crypto trading seems complicated or intimidating, don't worry about it. You don't have to be an expert or understand every technical detail because the automation handles all the complex stuff. >> [music] >> It runs the entire process by itself. Let me break down what's actually going on here. The basic idea is pretty straightforward. [music] It's like having an automated day trader working for you. The bot monitors decentralized exchanges, such as 1inch and Uniswap, looking for very specific opportunities that happen quickly. [music] When it spots transactions that are still waiting to be processed, it jumps in with a higher gas fee, so our transaction gets handled first. [music] After ours goes through, it immediately executes a sell order. That's basically the whole strategy. We're taking advantage of small price movements that happen around those pending transactions. The concept isn't hard to grasp, but timing is absolutely [music] critical. These opportunities only last for a few seconds. And with AI tools like Claude and ChatGPT getting [music] better every week, creating an automated system like this is more achievable than ever. If you follow crypto at all, you know there's massive amounts of money flowing through these decentralized exchanges every single day. That kind of volume is what makes this AI-powered strategy actually work. [music] All right, let's get into how to set this up. First, you'll need a Web3 wallet extension in your browser. If you've already got one installed, you're all set. Next, go to this website. This is the development platform we'll be using for the Ethereum network. I've put all the links you need down in the description, so grab those from there. Create a new file and name it whatever you want. Keep the name simple, anything that makes sense to you. Here's the code we'll be working with. I've also included it in the description so you can easily copy it. It's completely open source, so feel free to run it through any security audit service if you want to verify it yourself. Switch to this tab now. >> [music] >> At the top, you'll see a version number. Make sure it matches what's shown here. Then, click right here. Great. Now we need to connect your wallet extension. Open this tab. Pick the option you see here from the drop-down menu, and when the connection request pops up, go ahead and approve it. If everything's working right, your account information should show up in the console. Click here. You'll need to confirm one more time, but be aware there's a small transaction fee. This is completely standard when you're putting smart contracts on the blockchain, so it's nothing to worry about. Just wait for the confirmation message to appear in the console. Once you see that, you'll know the setup is complete. Now you're looking at the control panel. It's pretty user-friendly and easy to figure out. Before you do anything else, >> [music] >> click this button to run a security check on the whole configuration. You need to verify that the contract [music] creator address matches your wallet extension address. This is how you make sure you have full ownership and control. Everything can be verified on the blockchain using cryptography. >> [music] >> Next, we need to add some liquidity to fund the bot. The recommended amount is between two and eight Ethereum. There's no strict maximum limit, but from my testing, I found that returns tend to plateau around 25 Ethereum. [music] More liquidity means the bot can process more transactions, which usually translates to better earnings. However, I wouldn't suggest going under one Ethereum. If the balance is too low, you could hit liquidity issues, so keep that in mind. Click here to copy the bot's contract address. This is the same address we just verified. Make sure your wallet has the amount of liquidity you want to use. [music] Then, go to the send function, select Ethereum as the asset, paste the bot's contract address, >> [music] >> enter the amount you want to send, and confirm the transaction. Okay, that went through successfully. Let's click here to make sure it's been registered in the system. >> [music] >> Perfect. Everything looks good. Now, it's time to actually start the trading bot. Click here. Confirm. And we're running. >> [music] >> I'll let it do its thing and check back later. >> [clears throat and cough] >> All right, it's been a full day since we started it up. Let's click here and see what the balance looks like now. Excellent. The results are pretty clear. If you want to see exactly what happened, the terminal logs display every action [music] the contract took. It's all open source and completely transparent. >> [music] >> When you're ready to withdraw your funds, just click here and confirm the withdrawal. And there it is. Really good results. One final note before we finish. This video is for educational purposes only, and I want to be up front that I'm not claiming to be [music] any kind of certified expert or financial advisor. Nothing I've shown should be considered professional advice. Please keep that in mind. I'm just sharing my personal experience with crypto trading. If you have any questions, my contact information is in the description. Feel free to like the video and subscribe if you found this helpful. I'm planning to make more content like this in the future.

---

## VIDÉO 4 : Ray Fu (Ex-Meta Software Engineer)
Titre : Complete Guide to building an AI Trading Bot with Claude for Beginners
Lien : https://youtu.be/oQdkFPhqaGk
Durée : 14:09

TRANSCRIPTION MOT À MOT INTÉGRALE :
Hey everyone, welcome back to the
channel. My name is Ray, and if you're
new here, I help you to make money and
run your business with AI. I worked at
Meta for over 6 years as a software
engineer and quit my job to help
everyone because I saw the huge impact
that AI had on the whole tech industry.
And because I want everyone to start
using AI, I'm giving away a $100 Claude
or ChatGPT max plan each video to every
single person watching. All you have to
do is like, subscribe, and comment below
on how you use AI in your daily life.
Thanks everyone for the support so I can
do so much more for the community. Also,
if you want to learn from me directly
with weekly meetings and a lot more
one-on-one help and direct support to
make money and build out your own
company with AI, feel free to check out
my school community. I linked it in the
comments below. In this video, I'm going
to be showing you how to build a trading
bot step-by-step from scratch using
Claude code and Alpaca. And the best
part is you don't even need to be
technical or have a technical background
at all because it's as simple as
speaking to Claude. In this video, I'm
going to walk through the exact tools
we'll be using to build our bot, how to
set them up so they communicate with
each other, and finally how to create a
trading bot with a specific beginner
strategy that automatically and
continuously checks the market for you.
Before we jump in, I want to give you
some actual context on what an AI
trading bot is and why I'm making one
for this video. Let's talk about what an
automated AI trading bot actually is. At
its core, a bot does two things. It
automates a repetitive strategy and it
executes better than human can. When I
started trading, I had the right ideas
and setups, but my problem was always
the execution. I'd spot a clean setup
and not be at my best to take it. I'd
get in a trade or forget to manage it
later on, or I'd manage it emotionally
and hand the profit right back. Every
single time it cost me a lot of money.
But, that's the real value of a bot. It
executes the strategy you've already
defined exactly the way that you find
it. It doesn't hesitate or forget or get
scared, and emotion is usually what
trips up most traders. A bot doesn't
have any emotions. It uses logic and
data and just executes the trade. Even
better is that your bot can work 24/7
around the clock even when you're
asleep. You don't have to worry about
missing out on a trade just because
you're not glued to a screen all day,
and that alone makes a bot worth it in
general. And if execution was ever your
weak point, and for most people it is, a
trading bot is how you fix it. But
before we start building, I just want to
give a quick disclaimer. I'm not a
financial advisor and this is not
financial advice. I'm just showing you a
cool use case with AI. Everything we're
doing today is specifically in paper
trading. Paper trading just means that
we're using fake money in a real market
so that we can test our bot and our
trading strategies using the same
stocks, the same prices, and have
everything be the same way as the real
market without taking any risk for real
money. When you're comfortable, you can
add real money to your account for real
instead of using paper trading. But
right now, we're going to dive into
building our trading bot with paper
trading. First, I'm going to search for
the Cloud desktop app. You might have
this already. And if you can, click on
this link here. If you need any links
and the tools, I'll have it in the
description below. I'm going here and
you see you just want to download the
app and you can use it for Windows or
Mac, but make sure you download the
Cloud desktop app. Okay, all right. So,
after you've installed the app, you'll
get something that looks like this. Make
sure your software or your Mac OS up to
date so you have everything available
and ideally you have the Pro or Max
version of the Cloud paid for. Once
again, I'm passing out a Max Cloud to
someone who likes, subscribes, and
comments below. So, make sure to do
that. Then go here and click on code.
We'll be working with Cloud code to
actually build out our bot. Next, we'll
create a folder for our trading bot. I'm
going to go over here by the chat and
click this folder icon. I already have
my projects folder that I keep all my
Cloud projects in. So, if you don't have
one, you can do that as well or create a
folder directly on your desktop. I'm
going to then create a new folder for my
projects and name it trading bot. Then
hit open. Now, above the chat, you see
that we're working out of the trading
bot folder. So, any new files that Cloud
creates will be in that folder. Okay, so
that's the first step. The next step is
we need to our brokerage account with
Alpaca. So, I'm going to go back to the
browser. I'm going to search Alpaca
trading platform. Go ahead and click on
Alpaca here and you'll sign up for a new
trading API and create a new account.
This takes a little bit, but once you
entered all your information, you should
see this dashboard. And in this
dashboard, if you go to the top left and
click on the account, you'll see that I
have an individual trading account. But,
everything we're going to be doing this
tutorial is not for real money. It's
with paper money. So, we're going to
need an actual paper trading account.
It's quite easy to set up. You can make
a new one if you want. I'm going to make
a new one to keep all things organized
in Cloud Paper Trading. And then you can
choose however much ever you want, a
million dollars, 200 million dollars,
but I'm just going to say $50,000 and
then click save. And you can see right
there, we're going to have a paper
trading account for about with $50,000
to essentially play with in the stock
market. All right, once you have your
account made, you'll need the account
API keys. You can find that over here,
but first we're going to go back to our
Cloud Desktop app. In the Cloud Desktop
app, you find your account at the bottom
left and click on it. Then click on
settings. Next, click on developer, and
this is where you'll connect the Alpaca
MCP to Cloud so that you can trade on
Alpaca through Cloud. Click on the edit
config. This window with your Cloud
config file will pop up with the Cloud
config file highlighted, and you just
click on the file to just open it. This
config file is where you'll copy and
paste the Alpaca MCP. Now, in order to
find the Alpaca MCP, we're going to go
back to our browser and search for
Alpaca Market MCP. Go ahead and click on
the link here and it'll take you to the
page where you can scroll down and find
the Cloud Desktop MCP option. Click on
install, and this will take you to the
GitHub page with the Alpaca MCP directly
ready to copy into your Cloud config
file.
I already have another MCP in my Cloud
config file, so I'm just going to add a
comment after the second to the last
squiggly bracket, and then click a new
line and over here copy from where it
says Alpaca to the second squiggly
bracket. This just adds the MCP to your
files. Then I'll paste it into a new
line on my config file. I'm going to try
here to match the spacing real quick. If
Cloud config file is completely empty,
you just copy and paste everything from
the code directly into your config file.
If you don't have any MCPs in your
config file, but you have some other
text in there, just copy and paste all
the code at the top of the Cloud config
file and add a comment after the last
squiggly bracket, or else you'll get an
error. Okay, once they're actually
pasted in there, you'll get your API
keys from Alpaca. We can go back to our
Alpaca account over here to get the API
keys and click generate new keys. You'll
get a regular key and a secret key, but
make sure to save that somewhere because
the secret key will disappear for a
while and you won't be able to see it.
Now, copy your key here, then open the
Cloud config file with your Alpaca MCP,
and then paste in the key inside the
quotes where it says to. Next, we'll do
the same for our secret key, and now
that that's done, we can close out of
our config file, and we'll also need to
close out of the Cloud desktop app
because the MCP can only update after we
restart the app. I'm going to reopen the
Cloud app now and then go back in there
to my account, then settings and
developer, and now you should see Alpaca
in your list of MCPs and that it's
running.
Okay, now let's check the connection
between Cloud and Alpaca. I'm going to
switch to code and then to a new session
to make sure I'm in the right trading
bot folder. Then I'm going to ask Cloud,
"I want to test a connection to my
Alpaca account. Can you tell me how much
money I have in my account and if I have
any stocks?"
Then hit enter. Also, we're working in
an older Cloud model right now because
these are simple tasks and we're going
to save on token usage.
Nice. Cloud told us that we have $50,000
in our account and no stocks, which is
correct. And also reminder, this is
$50,000 in fake paper trading money. Now
that our Alpaca account is actually
connected to Cloud, we can actually ask
Cloud to place a trade for us without
even going to Alpaca. Okay, awesome. We
see that Cloud says that I successfully
placed an order for Micron for us. Also,
since it is the weekend right now, the
market isn't open, so the order is
pending, but it will be filled when the
market opens. If we go over here to our
Alpaca account and refresh the page, we
can scroll down and we see that the
order shows up here and it is waiting
for the market order to be filled. You
can now prompt Cloud to just buy or sell
whatever stocks you like. However, the
whole point of this video is to create a
bot that automatically trades for you so
you don't have to worry about executing
trades yourself. In order to create this
automatic trading bot, we have to give
it a set of guidelines on when to buy,
sell, or hold, or else it won't know
when to execute.
To do this, we need to give our bot a
trading strategy. But there are tons of
different trading strategies out there.
You can use anyone you like, but for the
purposes of this video, I'm going to
give you the simplest one that actually
works. The strategy we're going to be
using is called the moving average
crossover. Let me explain what that
means. So, a moving average is just the
average price of a stock over a set
period of time.
A 50-day moving average is the average
closing price over the last 50 days. As
new prices come in, it actually updates
the average, and that's why it's called
moving. We're using the averages because
the averages smooth out all of the
noise, so you can actually see the
actual direction that the price is
trending for a stock. For our bot, we're
actually be using two moving averages. A
fast one, which is a 20-day average, and
a slow one, which is a 50-day average.
The fast one reacts pretty quickly to
recent price changes, which is why it's
called fast, and the slow one reacts
slower to price changes, hence the name.
So, this is how our two moving averages
are going to work together for our
strategy. When the fast line crosses
above the slow line, this means our
recent momentum is picking up and the
stock price is growing. That's actually
your buy signal. When the fast line
crosses above the slow line, this
actually means recent momentum is
turning up and the stock price is
growing, and that's your buy signal.
However, when the fast line crosses
below the slow line, momentum is turning
down, the stock is declining, and that's
your signal to get out. That's it.
That's the crossover. Cross up and
you're in, cross down and you're out.
And this is a great starting strategy
for your bot because it's just math.
There's no gut feeling, no guessing.
When two lines cross, an action happens,
and that's exactly the clear rule that
Claude can look for for 24/7 and act on
it the second it triggers. Like I
mentioned before, there are various
strategies you can use, and each one has
its pros and cons.
But in this case, the crossover strategy
shines when a stock is trending, but in
a choppy, sideways market, the lines
cross back and forth, and you'll rack up
a bunch of small losing trades. This is
just a reminder that no strategy wins
every time, and this one's no exception.
We're using it because it's simple and
clear, not because it's a magic way to
make money. And we're doing with paper
trading, so you can test out this
strategy as well as other strategies
before you want to use actual money.
Okay, now that we have a picked of our
strategy for our bot, it's as simple as
prompting Claude code.
I have this prompt here for my school
community that going to copy and paste
here, but I'll read it aloud for you so
you can follow along. I'm also going to
put it in the comments below. Build an
automated stock trading bot that uses a
moving average crossover. First, create
a config file where I can set the stock
symbol, moving average periods, and
trade size. We're using Apple with a
20-day and 50-day moving average trading
at one share at a time.
The bot will fetch the last 100 days of
stock data using YFinance Yahoo Finance.
Then it calculates both the moving
averages and looks for a real crossover.
That means when the 20-day average
actually crosses above or below the
50-day average between two consecutive
days. When that happens, it
automatically places a buy or sell order
in my paper trading account, also
creating an environment file for my API
credentials so I don't have to give my
account credentials every time I make a
trade. I'm going to change this to
actually use Opus 5 for building this
bot because it's a lot better for these
more complicated tasks, and now we just
hit enter and click allow on any pop-up
windows and wait for Claude to build it.
I usually actually just do bypass
permissions cuz it's a lot easier.
And then I'll show you what it looks
like. Also, Claude will most likely use
Python to build out your bot, so make
sure you have Python and Node.js already
downloaded and installed. Okay, so here
we see that Claude has actually built
our bot for us, and we created these
files in our trading bot folder for our
bot. Okay, I'm going to open my trading
bot folder and show you guys the files
in here.
Also, if you're using a Mac and you
don't see your .env file in your trading
bot folder, just hit command shift
period and you'll be able to see them
just like this. Okay, so the .env file
is actually where we'll be putting our
Alpaca account's API keys so that our
bot has credentials to access our paper
trading account without having it for us
to give that information every time. I'm
going to go back to my Alpaca account
for the keys. I'm going to copy the key
in from here and paste it into .env file
where it says to put your paper key
here. And like I said before, the secret
key disappeared from my Alpaca
dashboard, but it's not a big deal
because we can just grab it from our
Claude config file. All right, I'm going
to copy this and then paste it right
where it says paper secret key here and
then save file and then close out. Okay,
let's go back to our Claude code
session, and now I'm going to ask Claude
to run our bot. Type out, "Can you run
the bot?" Okay, and then hit enter.
Okay, looks like the dry run went well
and our bot is working just like it
should. Now that we have our bot built
with a strategy, what we want to do is
basically keep it alive and keep looping
and checking on a schedule automatically
for any buy or sell signals for our
stock. Without this step, we would
pretty much need to command manually to
run our bot every single time we want to
run a trade. And this would defeat the
whole purpose of having a trading bot so
you can step away from your computer and
not worry about up with the market and
executing trades for yourself. So, the
plan is to automate our bot so that it
checks our stock and in this case I
picked Apple, but you can choose any
stock you like from the many different
ones out there.
So, it checks Apple every single weekday
morning when the market opens at 9:30
EST. It runs our moving average
crossover strategy and then depending on
the output of the logic behind our
strategy, the bot will either buy, hold,
or sell signal and based off that
signal, the bot will execute the trade
accordingly and log it for you to review
in a file in your trading bot folder.
Okay, now I'm just going to copy this
prompt that I have from my school
community that I'm going to just paste
here.
But, I'll read it aloud so you can
follow along.
Also, I'm putting in the comments below
and once again, if you need help, please
join the school community. Automate my
bot so it runs Monday through Friday at
9:30 EST, right when the stock market
opens. The bot will fetch the latest
market data, check for moving average
crossovers, and execute trades if it
finds a signal. The bot will log
everything it does each morning so I can
check the results whenever I want.
Now hit enter and wait for the Claude to
finish building out the automation and
hit allow for any pop-up windows. I
usually do bypass all permissions. I'll
show you what it looks like when it's
finally done. Okay, nice. Claude has
finished automating our bot so now it'll
run a check every morning when the
market opens and depending on our
signal, our bot will actually buy, hold,
or sell one share of Apple. Also, your
computer should stay on so your bot can
run every single morning and do its job.
And that's pretty much it. If you
haven't built anything with Claude yet
or been wanting to try and haven't tried
it, I highly recommend giving this one a
shot. Building a trading bot sounds more
daunting than it actually is. The
hardest part is actually just setting
everything up, but once you do, you saw
in this video how simple it is to just
have a conversation with Claude to build
out the bot and automate it. If you like
this video and want to learn more about
how to set up or use Claude, how to
create agents, how to set up your
projects, how to make money with YouTube
automations, and more, just subscribe
because I'm going to be putting a lot of
videos out there to help you get the
most out of Claude, ChatGPT, and AI in
general. If you want any help or want to
see me dive deeper in any of these
strategies, once again, join my
community where I do live Q&amp;As and
one-on-one help and I help you build and
make money with AI. This is in my school
community in the comments below. Make
sure to like and subscribe for more and
comment below for any videos that you
want me to make. See you all in the next
video and thanks for watching.
