A silly amazon product analysis tool using OpenAI and Browserbase. It recommends water flossers because this is what I was shopping for today.

Needless to say, this is just a toy to test Browserbase and a couple other libraries, not a serious recommendation tool.

Note that you'll need a paid Browserbase account to run this, so it could solve the Amazon CAPTCHA.

When it works, it looks something like this:

```sh
$ brew install uv
$ cp .env.example .env # fill in your API keys

$ uv sync
$ uv run main.py 
Session replay URL: https://browserbase.com/sessions/60b32717-cf31-4215-893f-62fb04bd464a
Searching Amazon for water flosser...
Found 48 products

Analyzing: https://amazon.com/dp/B0BG52SJ5N
Product: COSLUS Water Dental Flosser Teeth Pick: Portable Cordless Oral Irrigator 300ML Rechargeable Travel Irrigation Cleaner IPX7 Waterproof Electric Flossing Machine for Teeth Cleaning C20(F5020E)
Portable: True
Rechargeable: True
Brand Reputation: 4/5
Value Score: 9.0/10
Reasoning:
### Portability
The COSLUS Water Dental Flosser is explicitly described as being portable, with features emphasizing its compact and lightweight design. It is highlighted as suitable for home and travel use, and it includes a USB cable for convenient charging, which strongly supports its portability. Therefore, the product is considered portable.

### Rechargeability
This product is rechargeable as it boasts a powerful rechargeable battery with a battery indicator, and it mentions an impressive 30-day battery life after a 3-hour charge. The inclusion of a USB cable for charging also confirms this feature, thus, it is classified as rechargeable.

### Value Assessment
The COSLUS Water Dental Flosser offers a robust set of features: a large 300ml water tank, advanced water pulse technology, multiple operation modes, and pressure settings. The tank's capacity is notable, as it requires less frequent refilling compared to smaller models, enhancing user convenience. A 30-day battery life with quick charging adds to its portability benefits. Its IPX7 waterproof certification and a three-year durability claim suggest good construction and reliability. With a price of $38.79, it compares favorably against market norms for similar functionality. Overall, these features make it a strong value product, meriting a score of 9.

### Brand Reputation
COSLUS has a well-established reputation, evidenced by the substantial number of reviews (31,340) and a high rating of 4.4 out of 5 stars. While COSLUS may not be an industry leader, the positive product reception and its evaluation by an American dental team suggest a good reputation in the market. Therefore, the brand reputation score is assessed at 4.

Done
```
