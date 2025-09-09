# Yelp Restaurants Dataset for Multi-Agent System Practice

This dataset is designed for practicing the development of multi-agent systems for restaurant recommendation and reservation. The original data is sourced from the [Yelp Open Dataset](https://business.yelp.com/data/resources/open-dataset/) and contains only restaurants (759) from the Santa Barbara area.

## Data File
- **restaurants.json**: A JSON file containing key information, reviews, photos, and attributes for restaurants in Santa Barbara.

## Data Structure
Each restaurant object includes the following fields:

- **id**: Unique restaurant ID
- **name**: Restaurant name
- **address, city, state, postal_code, location**: Address & location information
- **categories**: Restaurant categories (e.g., 'Italian', 'Mexican', 'Sushi Bars', etc.)
- **stars**: Average rating (up to 5 stars)
- **review_count**: Total number of reviews
- **attributes**: Various additional properties
    - ambiences: ['casual', 'classy', ...] (atmosphere)
    - good_for_meals: ['breakfast', 'brunch', ...] (meal times)
    - parkings: ['garage', 'lot', ...] (parking options)
    - good_for_kids, corkage, drive_thru, has_tv, dogs_allowed, wifi, good_for_dancing, happy_hour, smoking (true/false)
- **photos**: List of related photos (photo_id matches the filename in the photos folder)
- **tips**: User-submitted tips
- **reviews**: User-submitted reviews and ratings

## Example Use Cases
- Developing restaurant recommendation algorithms
- Testing reservation system scenarios
- Filtering and searching based on user preferences
- Simulating multi-agent cooperation and competition

## Reference
- Original data: [Yelp Open Dataset](https://business.yelp.com/data/resources/open-dataset/)
- This dataset is for educational and research purposes only.
