DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS posts;
DROP TABLE IF EXISTS rooms;
DROP TABLE IF EXISTS votes;


CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT, 
  user_id TEXT UNIQUE NOT NULL,      
  nickname TEXT NOT NULL,
  password TEXT NOT NULL       
);



CREATE TABLE rooms (
  id INTEGER PRIMARY KEY AUTOINCREMENT, 
  create_user_id INTEGER NOT NULL,          
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  room_name TEXT UNIQUE NOT NULL,     
  password TEXT NOT NULL ,             
  FOREIGN KEY (create_user_id) REFERENCES users (id) 
);



CREATE TABLE posts (
  id INTEGER PRIMARY KEY AUTOINCREMENT, 
  author_id INTEGER NOT NULL,           
  room_id INTEGER NOT NULL,           
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,  
  main TEXT NOT NULL,             
  edit INTEGER NOT NULL,
  public INTEGER NOT NULL,
  FOREIGN KEY (author_id) REFERENCES users (id),  
  FOREIGN KEY (room_id) REFERENCES rooms (id)
);



CREATE TABLE votes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,  
  post_id INTEGER NOT NULL,        
  user_id INTEGER NOT NULL,
  room_id INTEGER NOT NULL,
  FOREIGN KEY (post_id) REFERENCES posts (id),  
  FOREIGN KEY (user_id) REFERENCES users (id),
  FOREIGN KEY (room_id) REFERENCES rooms (id)
);


