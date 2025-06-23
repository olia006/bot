# Car Rental Telegram Bot

A Telegram bot for car rental services with features including:
- Car fleet browsing
- Reservation system
- Review system
- Multi-language support (English, Spanish, Russian)
- Admin panel

## Environment Variables

The following environment variables need to be set in Render:

- `BOT_TOKEN`: Your Telegram bot token
- `ADMIN_USER_ID`: Admin user ID for special privileges

## Deployment Instructions

1. Fork or clone this repository
2. Create a new Web Service in Render
3. Connect your repository
4. Set the environment variables
5. Deploy!

## Development

To run locally:

1. Create a `.env` file with required variables
2. Install dependencies: `pip install -r requirements.txt`
3. Run the bot: `python3 bot.py`

## Features

- Browse cars by category (Economy, SUV, Premium)
- Make reservations with date selection
- View car details and images
- Process payments
- Leave reviews and ratings
- Admin dashboard for management

## Requirements

- Python 3.8+
- python-telegram-bot==20.7
- python-dotenv==1.0.0
- SQLite3

## Installation

1. Clone the repository
2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set up environment variables:

```bash
cp env_example.txt .env
```

Edit `.env` with your Telegram Bot Token and admin user ID.

## Usage

1. Start the bot:

```bash
python bot.py
```

2. Open Telegram and search for your bot
3. Start interacting with `/start`

## Car Categories

### Economy
- Chevrolet Cavalier: $49,990 CLP/day
- Cherry Tiggo 2 Pro Max: $49,990 CLP/day
- Honda Accord: $34,990 CLP/day
- Mazda 6: $49,990 CLP/day
- Subaru Impreza: $49,990 CLP/day
- Lexus ES 350: $54,990 CLP/day

### SUV
- Mazda CX-9: $119,990 CLP/day
- Mitsubishi Outlander: $71,990 CLP/day
- Subaru Outback: $64,990 CLP/day
- Toyota RAV4: $71,990 CLP/day

### Premium
- GAC All New GS8 (White): $149,990 CLP/day
- GAC All New GS8 (Black): $149,990 CLP/day
- Lexus RX 450 H: $135,990 CLP/day

## Discounts

- 3+ days: 15% off
- 30+ days: 25% off
- 90+ days: 35% off

## Admin Commands

- `/admin` - Access admin panel
- `/stats` - View rental statistics
- `/backup` - Create database backup

## Support

For support, please contact:
- Email: support@example.com
- Telegram: [@support_handle](https://t.me/support_handle)

## License

This project is licensed under the MIT License.

## Contributing

1. Fork the repository
2. Create your feature branch
3. Submit a pull request

## Security

- Environment variables for sensitive data
- Input validation
- Admin authentication
- Database security measures

## Updates

Check [CHANGELOG.md](CHANGELOG.md) for version history. 