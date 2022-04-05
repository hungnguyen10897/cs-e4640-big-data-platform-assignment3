import os, json, random, time
from pathlib import Path
from kafka import KafkaProducer

# Return file object of the data file
# skip the first row cotaining column names
def open_data_file(file_name, data_dir):
  f = open(data_dir.joinpath(file_name), "r")
  # Skip the first row
  f.readline()
  return f


def parse_line(line):
  stripped = line.strip("\n")
  parts = stripped.split("\t")
  parsed_dict = {
    "marketplace"	: parts[0],
    "customer_id" : parts[1],
    "review_id"	: parts[2],
    "product_id": parts[3],
    "product_parent"	: parts[4],
    "product_title"	: parts[5],
    "product_category"	: parts[6],
    "star_rating"	: int(parts[7]),
    "helpful_votes"	: int(parts[8]),
    "total_votes"	: int(parts[9]),
    "vine"	: parts[10],
    "verified_purchase": parts[11],
    "review_headline"	: parts[12],
    "review_body"	: parts[13],
    "review_date": parts[14]
  }
  return parsed_dict


def send_message(parsed_dict, producer):
  product_category = parsed_dict["product_category"]
  topic = product_category.replace(" ","_").replace("-","_").lower()
  msg_key = "event"
  msg_value = json.dumps(parsed_dict)

  try:
      key_bytes = bytes(msg_key, encoding='utf-8')
      value_bytes = bytes(msg_value, encoding='utf-8')
      producer.send(topic, key=key_bytes, value=value_bytes)
      producer.flush()
      print(f"Message published to topic '{topic}' successfully.")
  except Exception as ex:
      print(f"Exception when publishing message to topic '{topic}'")
      print(str(ex))


if __name__ == "__main__":

  MESSAGE_SPEED = 0 # sec/msg
  producer = KafkaProducer(bootstrap_servers='localhost:29092')

  data_dir = Path("./data")
  
  # Get all data files under data/
  _,_,files = next(os.walk(data_dir))

  file_objs = set(map(lambda file_name: open_data_file(file_name, data_dir), files))

  while(True):
    f = random.choice(list(file_objs))
    line = f.readline()
    if line == "":
      file_objs.remove(f)
      if len(file_objs) == 0:
        break
      continue
    parsed_dict = parse_line(line)
    send_message(parsed_dict, producer)

    time.sleep(MESSAGE_SPEED)

    # #
    # i = input("Continue?")
    # print("\n")
    # if i != "": break
