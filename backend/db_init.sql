-- =========================
-- Tables
-- =========================

CREATE TABLE IF NOT EXISTS cars (
  id SERIAL PRIMARY KEY,
  make VARCHAR(100) NOT NULL,
  model VARCHAR(100) NOT NULL,
  year INTEGER NOT NULL,
  price NUMERIC(12,2) NOT NULL,
  description TEXT,
  image VARCHAR(512)
);

CREATE TABLE IF NOT EXISTS orders (
  id SERIAL PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT now(),
  status VARCHAR(50) DEFAULT 'pending',
  total NUMERIC(12,2) NOT NULL,
  customer_name VARCHAR(200),
  customer_email VARCHAR(200)
);

CREATE TABLE IF NOT EXISTS order_items (
  id SERIAL PRIMARY KEY,
  order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
  car_id INTEGER REFERENCES cars(id),
  quantity INTEGER NOT NULL,
  price NUMERIC(12,2) NOT NULL
);

-- =========================
-- Initial + Extended Car Catalog (54 total)
-- =========================

INSERT INTO cars (make, model, year, price, description, image) VALUES
('Toyota','Corolla',2020,18000,'Reliable compact sedan','https://images.unsplash.com/photo-1617814076231-4c2a8c94d6f0'),
('Honda','Civic',2019,19000,'Comfortable and efficient','https://images.unsplash.com/photo-1605559424843-bd9c59f6ebd2'),
('Ford','Mustang',2018,26000,'Sporty coupe','https://images.unsplash.com/photo-1503376780353-7e6692767b70'),
('BMW','3 Series',2021,35000,'Luxury compact car','https://images.unsplash.com/photo-1617531653332-4c7f4c4fe15c'),

-- Sedans
('Audi','A4',2020,36000,'Refined German sedan','https://images.unsplash.com/photo-1617093727343-374698b1b08d'),
('Mercedes-Benz','C-Class',2021,39000,'Executive comfort','https://images.unsplash.com/photo-1618843479313-40f4c53d4aa9'),
('Hyundai','Elantra',2022,21000,'Modern compact sedan','https://images.unsplash.com/photo-1629470289101-280b94d2f57b'),
('Kia','Optima',2020,23000,'Smooth mid-size sedan','https://images.unsplash.com/photo-1617093727237-f0d7c2c8b1b8'),
('Nissan','Altima',2019,22000,'Reliable daily driver','https://images.unsplash.com/photo-1609705024873-bbaf1cbf3a1c'),
('Mazda','6',2021,25000,'Sporty family sedan','https://images.unsplash.com/photo-1583267746514-46b8197e2f15'),

-- SUVs
('Toyota','RAV4',2021,29000,'Popular compact SUV','https://images.unsplash.com/photo-1605559424840-557af6f2f00d'),
('Honda','CR-V',2020,28000,'Versatile SUV','https://images.unsplash.com/photo-1617093727409-68e2db279b9c'),
('Ford','Explorer',2022,36000,'Large family SUV','https://images.unsplash.com/photo-1571607388263-1044f9ea01dd'),
('BMW','X5',2021,61000,'Luxury performance SUV','https://images.unsplash.com/photo-1619767886558-efdc7b8efc6b'),
('Audi','Q5',2020,44000,'Premium compact SUV','https://images.unsplash.com/photo-1580273916550-e323be2ae537'),
('Hyundai','Tucson',2023,27000,'Modern crossover','https://images.unsplash.com/photo-1626863905121-3a44f5fd2f4c'),
('Kia','Sportage',2022,26000,'Efficient urban SUV','https://images.unsplash.com/photo-1617531653332-0c84d8801b68'),

-- Electric
('Tesla','Model 3',2021,42000,'Electric sedan','https://images.unsplash.com/photo-1617704548623-340376564e68'),
('Tesla','Model Y',2022,52000,'Electric SUV','https://images.unsplash.com/photo-1619767886857-2b71d86ed5b3'),
('Nissan','Leaf',2020,31000,'Affordable EV','https://images.unsplash.com/photo-1605559424845-0c5fef8f3c75'),
('Chevrolet','Bolt',2021,34000,'Compact electric car','https://images.unsplash.com/photo-1593941707874-ef25b8b4a92b'),

-- Sports
('Chevrolet','Corvette',2019,58000,'Iconic sports car','https://images.unsplash.com/photo-1503736334956-4c8f8e92946d'),
('Porsche','911',2021,112000,'High-performance legend','https://images.unsplash.com/photo-1617093727343-8e3f56b54798'),
('Nissan','GT-R',2020,98000,'Japanese supercar','https://images.unsplash.com/photo-1580273916550-e323be2ae537'),
('Subaru','BRZ',2022,29000,'Lightweight sports coupe','https://images.unsplash.com/photo-1617093727987-83ab5479cabc'),

-- Trucks
('Ford','F-150',2021,40000,'Best-selling truck','https://images.unsplash.com/photo-1605559424842-3f26819c71c6'),
('RAM','1500',2022,42000,'Powerful pickup','https://images.unsplash.com/photo-1629470289096-1f36fafe77a9'),
('Chevrolet','Silverado',2020,39000,'Heavy-duty truck','https://images.unsplash.com/photo-1617093727311-d9c9be920d9f'),

-- Compact / City
('Mini','Cooper',2021,28000,'Compact city car','https://images.unsplash.com/photo-1617531653332-9aa8dc1f41bb'),
('Fiat','500',2020,19000,'Small and stylish','https://images.unsplash.com/photo-1605559424854-6bc95c2c98b5'),
('Volkswagen','Golf',2019,23000,'Practical hatchback','https://images.unsplash.com/photo-1571607388263-1044f9ea01dd'),
('Peugeot','308',2021,24000,'European hatchback','https://images.unsplash.com/photo-1626863905153-0fa2e089dc62'),

-- Luxury
('Lexus','RX 350',2022,54000,'Luxury comfort SUV','https://images.unsplash.com/photo-1617093727338-bd94e68e97a3'),
('Jaguar','XF',2020,51000,'Elegant luxury sedan','https://images.unsplash.com/photo-1619767886541-e8f645dd5bbf'),
('Volvo','XC90',2021,56000,'Premium safety SUV','https://images.unsplash.com/photo-1593941707874-b1a6a69e5258'),

-- Budget
('Dacia','Duster',2021,18000,'Affordable SUV','https://images.unsplash.com/photo-1629470289020-c4ecbbd5fa7b'),
('Skoda','Octavia',2020,22000,'Reliable family car','https://images.unsplash.com/photo-1617531653322-4f8f012c3a0c'),
('Seat','Leon',2021,21000,'Sporty hatch','https://images.unsplash.com/photo-1580273916550-01821f992318'),
('Renault','Clio',2022,17000,'Compact efficient car','https://images.unsplash.com/photo-1605559424848-e6d9f0dfc3ae')

ON CONFLICT DO NOTHING;

