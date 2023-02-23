categories_list = ['application', 'big_data', 'compute', 'container', 'database', 'md', 'network', 'security-services', 'storage']

def transform_category_name(category_name):
    cat_name = category_name.replace("_", " ").replace("-", " ").capitalize()
    return cat_name

categories = {}
for category in categories_list:
    categories[category] = transform_category_name(category)

print(categories.values())

#for category in categories:
#    print(categories[category])

test_cat = 'application'

print(categories[test_cat])