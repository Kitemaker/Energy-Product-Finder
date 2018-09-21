# Alexa Skill: Energy-Product-Finder

## Inspiration
We need to find energy efficient electrical product to save energy and reduce the electricity consumption.

ENERGY STAR® ( https://www.energystar.gov/about) is the government-backed symbol for energy efficiency, providing simple, credible, and unbiased information that consumers and businesses rely on to make well-informed decisions. Thousands of industrial, commercial, utility, state, and local organizations—including more than 40 percent of the Fortune 500®—rely on their partnership with the U.S. Environmental Protection Agency (EPA) to deliver cost-saving energy efficiency solutions. evaluated and certified by ENERGY STAR 

To understand the product and its various properties we need to find the efficient products available in the market. 

## What it does
 "Energy STAR" provides Data Sets API for the developers (https://www.energystar.gov/productfinder/advanced). This
Data sets can be accessed using an access key and DataSet ID using python package 'sodapy"

Alexa skill   "Energy Product Finder" finds the energy efficient product e.g. Bulb, Fan, AC, or Refrigerator based on the parameters provided by the user. Therefore user can search any time a good energy saving product on the go also can understand the product better by visiting website of ENERGY STAR

## How I built it
I have created an Alexa-Skill using python sdk  "ask-sdk" and based on Dialog Management  to take the input for the type of Product and the parameters of the product
Then python package "sodapy" is used to make query to the API provided  by energystar.com  to fetch the best suited item based on the search criterion. At present I am using four products: Light Bulb, Ceiling Fan, Air Conditioner and Refrigerator.   Once product is find by the sodapy query then details of product is returned by Alexa Skill. 
 
## Challenges I ran into

Using Alexa Skill Dialog Management and Python SDK for Alexa Skill. 

## Accomplishments that I'm proud of

I self learned Developing Alexa Skill by using videos on You tube and documentation given on Alexa Developer Console . Learned and used Python SDK for Alexa Skill i.e. "ask-sdk" and created my first ever Alexa Skill

## What I learned

I have learnt lot of skills (i) ask-sdk  (ii) Dialog Management (iii) Slots  (iv) Amazon Lambda functions.

## What's next for Energy Efficient Product Finder

More Products shall be added with E Mail and SMS integration also Energy Saving Tips and How to Design
Home to save energy. Thanks to the Open Source Data Set provided by energystar.com
