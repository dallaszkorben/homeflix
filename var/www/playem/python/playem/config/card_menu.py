import os
import configparser
from pathlib import Path
import logging

from flask import session

from playem.property.property import Property

class CardMenu( Property ):
    HOME = str(Path.home())
    FOLDER = ".playem"
    CARD_MENU_FILE_NAME = "card_menu.yaml"

    __instance = None

    def __new__(cls):
        if cls.__instance == None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    @classmethod
    def getInstance(cls):
        inst = cls.__new__(cls)
        cls.__init__(cls.__instance)
        return inst

    def __init__(self):
        self.card_menu_path = os.path.join(CardMenu.HOME, CardMenu.FOLDER)
        file_full_path = os.path.join(self.card_menu_path, CardMenu.CARD_MENU_FILE_NAME)
        super().__init__( file_full_path)
        try:
            self.card_menu_dict = self.getDict()
        except FileNotFoundError:
            self.card_menu_dict = self.buildCardMenuDict()

    def buildCardMenuDict(self):
        card_menu_dict = {
              "default": {
                "extends": "Generator",
                "is_thumbnail_show_synchronous": true,
                "name": "main_menu",
                "container_list": [
                  {
                    "order": 0,
                    "static_hard_coded": {
                      "container_title_key": "categories",
                      "thumbnails": [
                        {
                          "order": 0,
                          "thumbnail": {
                            "image": "images/categories/movie.jpg",
                            "title_key": "movies"
                          },
                          "description": {
                            "image": "images/categories/movie.jpg",
                            "title_key": "movies"
                          },
                          "history": {
                            "title_key": "movies"
                          },
                          "execution": {
                            "extends": "GeneralRestGenerator",
                            "is_thumbnail_show_synchronous": true,
                            "name": "movie",
                            "container_list": [
                              {
                                "order": 0,
                                "static_hard_coded": {
                                  "container_title_key": "movies",
                                  "thumbnails": [
                                    {
                                      "order": 0,
                                      "thumbnail": {
                                        "image": "images/categories/movie_mixed.jpg",
                                        "title_key": "movie_mixed"
                                      },
                                      "description": {
                                        "image": "images/categories/movie_mixed.jpg",
                                        "title_key": "movie_mixed"
                                      },
                                      "history": {
                                        "title_key": "movie_mixed"
                                      },
                                      "execution": {
                                        "extends": "GeneralRestGenerator",
                                        "is_thumbnail_show_synchronous": true,
                                        "name": "movie_filter",
                                        "container_list": [
                                          {
                                            "order": 0,
                                            "static_hard_coded": {
                                              "container_title_key": "movie_filter",
                                              "thumbnails": [
                                                {
                                                  "order": 0,
                                                  "thumbnail": {
                                                    "image": "images/categories/movie_by_genre.jpg",
                                                    "title_key": "movie_by_genre"
                                                  },
                                                  "description": {
                                                    "image": "images/categories/movie_by_genre.jpg",
                                                    "title_key": "movie_by_genre"
                                                  },
                                                  "history": {
                                                    "title_key": "movie_by_genre"
                                                  },
                                                  "execution": {
                                                    "extends": "GeneralRestGenerator",
                                                    "is_thumbnail_show_synchronous": false,
                                                    "name": "movie_genre",
                                                    "container_list": [
                                                      {
                                                        "order": 0,
                                                        "dynamic_hard_coded": {
                                                          "title": {
                                                            "dict_translator": "translated_genre_movie",
                                                            "id": "drama"
                                                          },
                                                          "data": {
                                                            "category": "movie",
                                                            "genres": "drama_AND__NOT_comedy_AND__NOT_war_AND__NOT_satire_AND__NOT_crime_AND__NOT_thriller_AND__NOT_fantasy_AND__NOT_music_AND__NOT_scifi_AND__NOT_horror"
                                                          },
                                                          "request": {
                                                            "static": true,
                                                            "method": "GET",
                                                            "protocol": "http",
                                                            "path": "/collect/highest/mixed"
                                                          }
                                                        }
                                                      },
                                                      {
                                                        "order": 1,
                                                        "dynamic_hard_coded": {
                                                          "title": {
                                                            "dict_translator": "translated_genre_movie",
                                                            "id": "scifi"
                                                          },
                                                          "data": {
                                                            "category": "movie",
                                                            "genres": "scifi_AND__NOT_trash"
                                                          },
                                                          "request": {
                                                            "static": true,
                                                            "method": "GET",
                                                            "protocol": "http",
                                                            "path": "/collect/highest/mixed"
                                                          }
                                                        }
                                                      },
                                                      {
                                                        "order": 2,
                                                        "dynamic_hard_coded": {
                                                          "title": {
                                                            "dict_translator": "translated_genre_movie",
                                                            "id": "fantasy"
                                                          },
                                                          "data": {
                                                            "category": "movie",
                                                            "genres": "fantasy"
                                                          },
                                                          "request": {
                                                            "static": true,
                                                            "method": "GET",
                                                            "protocol": "http",
                                                            "path": "/collect/highest/mixed"
                                                          }
                                                        }
                                                      },
                                                      {
                                                        "order": 3,
                                                        "dynamic_hard_coded": {
                                                          "title": {
                                                            "dict_translator": "translated_genre_movie",
                                                            "id": "comedy"
                                                          },
                                                          "data": {
                                                            "category": "movie",
                                                            "genres": "comedy_AND__NOT_teen"
                                                          },
                                                          "request": {
                                                            "static": true,
                                                            "method": "GET",
                                                            "protocol": "http",
                                                            "path": "/collect/highest/mixed"
                                                          }
                                                        }
                                                      },
                                                      {
                                                        "order": 4,
                                                        "dynamic_hard_coded": {
                                                          "title": {
                                                            "dict_translator": "translated_genre_movie",
                                                            "id": "teen"
                                                          },
                                                          "data": {
                                                            "category": "movie",
                                                            "genres": "teen"
                                                          },
                                                          "request": {
                                                            "static": true,
                                                            "method": "GET",
                                                            "protocol": "http",
                                                            "path": "/collect/highest/mixed"
                                                          }
                                                        }
                                                      },
                                                      {
                                                        "order": 5,
                                                        "dynamic_hard_coded": {
                                                          "title": {
                                                            "dict_translator": "translated_genre_movie",
                                                            "id": "satire"
                                                          },
                                                          "data": {
                                                            "category": "movie",
                                                            "genres": "satire"
                                                          },
                                                          "request": {
                                                            "static": true,
                                                            "method": "GET",
                                                            "protocol": "http",
                                                            "path": "/collect/highest/mixed"
                                                          }
                                                        }
                                                      },
                                                      {
                                                        "order": 6,
                                                        "dynamic_hard_coded": {
                                                          "title": {
                                                            "dict_translator": "translated_genre_movie",
                                                            "id": "crime"
                                                          },
                                                          "data": {
                                                            "category": "movie",
                                                            "genres": "crime_AND__NOT_trash"
                                                          },
                                                          "request": {
                                                            "static": true,
                                                            "method": "GET",
                                                            "protocol": "http",
                                                            "path": "/collect/highest/mixed"
                                                          }
                                                        }
                                                      },
                                                      {
                                                        "order": 7,
                                                        "dynamic_hard_coded": {
                                                          "title": {
                                                            "dict_translator": "translated_genre_movie",
                                                            "id": "action"
                                                          },
                                                          "data": {
                                                            "category": "movie",
                                                            "genres": "action_AND__NOT_trash"
                                                          },
                                                          "request": {
                                                            "static": true,
                                                            "method": "GET",
                                                            "protocol": "http",
                                                            "path": "/collect/highest/mixed"
                                                          }
                                                        }
                                                      },
                                                      {
                                                        "order": 8,
                                                        "dynamic_hard_coded": {
                                                          "title": {
                                                            "dict_translator": "translated_genre_movie",
                                                            "id": "thriller"
                                                          },
                                                          "data": {
                                                            "category": "movie",
                                                            "genres": "thriller"
                                                          },
                                                          "request": {
                                                            "static": true,
                                                            "method": "GET",
                                                            "protocol": "http",
                                                            "path": "/collect/highest/mixed"
                                                          }
                                                        }
                                                      },
                                                      {
                                                        "order": 9,
                                                        "dynamic_hard_coded": {
                                                          "title": {
                                                            "dict_translator": "translated_genre_movie",
                                                            "id": "horror"
                                                          },
                                                          "data": {
                                                            "category": "movie",
                                                            "genres": "horror"
                                                          },
                                                          "request": {
                                                            "static": true,
                                                            "method": "GET",
                                                            "protocol": "http",
                                                            "path": "/collect/highest/mixed"
                                                          }
                                                        }
                                                      },
                                                      {
                                                        "order": 10,
                                                        "dynamic_hard_coded": {
                                                          "title": {
                                                            "dict_translator": "translated_genre_movie",
                                                            "id": "western"
                                                          },
                                                          "data": {
                                                            "category": "movie",
                                                            "genres": "western"
                                                          },
                                                          "request": {
                                                            "static": true,
                                                            "method": "GET",
                                                            "protocol": "http",
                                                            "path": "/collect/highest/mixed"
                                                          }
                                                        }
                                                      },
                                                      {
                                                        "order": 11,
                                                        "dynamic_hard_coded": {
                                                          "title": {
                                                            "dict_translator": "translated_genre_movie",
                                                            "id": "war"
                                                          },
                                                          "data": {
                                                            "category": "movie",
                                                            "genres": "war"
                                                          },
                                                          "request": {
                                                            "static": true,
                                                            "method": "GET",
                                                            "protocol": "http",
                                                            "path": "/collect/highest/mixed"
                                                          }
                                                        }
                                                      },
                                                      {
                                                        "order": 12,
                                                        "dynamic_hard_coded": {
                                                          "title": {
                                                            "dict_translator": "translated_genre_movie",
                                                            "id": "music"
                                                          },
                                                          "data": {
                                                            "category": "movie",
                                                            "genres": "music"
                                                          },
                                                          "request": {
                                                            "static": true,
                                                            "method": "GET",
                                                            "protocol": "http",
                                                            "path": "/collect/highest/mixed"
                                                          }
                                                        }
                                                      },
                                                      {
                                                        "order": 13,
                                                        "dynamic_hard_coded": {
                                                          "title": {
                                                            "dict_translator": "translated_genre_movie",
                                                            "id": "history"
                                                          },
                                                          "data": {
                                                            "category": "movie",
                                                            "genres": "history"
                                                          },
                                                          "request": {
                                                            "static": true,
                                                            "method": "GET",
                                                            "protocol": "http",
                                                            "path": "/collect/highest/mixed"
                                                          }
                                                        }
                                                      },
                                                      {
                                                        "order": 14,
                                                        "dynamic_hard_coded": {
                                                          "title": {
                                                            "dict_translator": "translated_genre_movie",
                                                            "id": "documentary"
                                                          },
                                                          "data": {
                                                            "category": "movie",
                                                            "genres": "documentary"
                                                          },
                                                          "request": {
                                                            "static": true,
                                                            "method": "GET",
                                                            "protocol": "http",
                                                            "path": "/collect/highest/mixed"
                                                          }
                                                        }
                                                      },
                                                      {
                                                        "order": 15,
                                                        "dynamic_hard_coded": {
                                                          "title": {
                                                            "dict_translator": "translated_genre_movie",
                                                            "id": "trash"
                                                          },
                                                          "data": {
                                                            "category": "movie",
                                                            "genres": "trash"
                                                          },
                                                          "request": {
                                                            "static": true,
                                                            "method": "GET",
                                                            "protocol": "http",
                                                            "path": "/collect/highest/mixed"
                                                          }
                                                        }
                                                      }
                                                    ]
                                                  }
                                                },
                                                {
                                                  "order": 2,
                                                  "thumbnail": {
                                                    "image": "images/categories/movie_by_director.jpg",
                                                    "title_key": "movie_by_director"
                                                  },
                                                  "description": {
                                                    "image": "images/categories/movie_by_director.jpg",
                                                    "title_key": "movie_by_director"
                                                  },
                                                  "history": {
                                                    "title_key": "movie_by_director"
                                                  },
                                                  "execution": {
                                                    "extends": "GeneralRestGenerator",
                                                    "is_thumbnail_show_synchronous": false,
                                                    "name": "movie_genre",
                                                    "container_list": [
                                                      {
                                                        "order": 0,
                                                        "dynamic_queried": {
                                                          "pre_query": {
                                                            "data": {
                                                              "category": "movie",
                                                              "minimum": 2,
                                                              "limit": 40
                                                            },
                                                            "request": {
                                                              "static": "-not_needed-",
                                                              "method": "GET",
                                                              "protocol": "http",
                                                              "path": "/collect/directors/by/movie/count"
                                                            }
                                                          },
                                                          "query_loop": {
                                                            "data": {
                                                              "category": "movie"
                                                            },
                                                            "data_from_pre_response_list": {
                                                              "type": "value",
                                                              "value": "directors"
                                                            },
                                                            "request": {
                                                              "static": false,
                                                              "method": "GET",
                                                              "protocol": "http",
                                                              "path": "/collect/highest/mixed"
                                                            },
                                                            "title": {
                                                              "dict_translator": null,
                                                              "id": "name"
                                                            }
                                                          }
                                                        }
                                                      }
                                                    ]
                                                  }
                                                }
                                              ]
                                            }
                                          }
                                        ]
                                      }
                                    },
                                    {
                                      "order": 4,
                                      "thumbnail": {
                                        "image": "images/categories/movie_playlists.jpg",
                                        "title_key": "movie_playlists"
                                      },
                                      "description": {
                                        "image": "images/categories/movie_playlists.jpg",
                                        "title_key": "movie_playlists"
                                      },
                                      "history": {
                                        "title_key": "movie_playlists"
                                      },
                                      "execution": {
                                        "extends": "GeneralRestGenerator",
                                        "is_thumbnail_show_synchronous": false,
                                        "name": "movie_playlist",
                                        "container_list": [
                                          {
                                            "order": 0,
                                            "dynamic_hard_coded": {
                                              "title": {
                                                "dict_translator": "translated_titles",
                                                "id": "movie_interrupted"
                                              },
                                              "data": {
                                                "category": "movie",
                                                "playlist": "interrupted"
                                              },
                                              "request": {
                                                "static": true,
                                                "method": "GET",
                                                "protocol": "http",
                                                "path": "/collect/lowest"
                                              }
                                            }
                                          },
                                          {
                                            "order": 1,
                                            "dynamic_hard_coded": {
                                              "title": {
                                                "dict_translator": "translated_titles",
                                                "id": "movie_last_watched"
                                              },
                                              "data": {
                                                "category": "movie",
                                                "playlist": "last_watched"
                                              },
                                              "request": {
                                                "static": true,
                                                "method": "GET",
                                                "protocol": "http",
                                                "path": "/collect/lowest"
                                              }
                                            }
                                          },
                                          {
                                            "order": 2,
                                            "dynamic_hard_coded": {
                                              "title": {
                                                "dict_translator": "translated_titles",
                                                "id": "movie_most_watched"
                                              },
                                              "data": {
                                                "category": "movie",
                                                "playlist": "most_watched"
                                              },
                                              "request": {
                                                "static": true,
                                                "method": "GET",
                                                "protocol": "http",
                                                "path": "/collect/lowest"
                                              }
                                            }
                                          },
                                          {
                                            "order": 3,
                                            "dynamic_queried": {
                                              "pre_query": {
                                                "data": {
                                                  "category": "movie"
                                                },
                                                "request": {
                                                  "static": "-not_needed-",
                                                  "method": "GET",
                                                  "protocol": "http",
                                                  "path": "/personal/tag/get"
                                                }
                                              },
                                              "query_loop": {
                                                "data": {
                                                  "category": "movie"
                                                },
                                                "data_from_pre_response_list": {
                                                  "type": "dict",
                                                  "dict": {
                                                    "tags": "name"
                                                  }
                                                },
                                                "request": {
                                                  "static": false,
                                                  "method": "GET",
                                                  "protocol": "http",
                                                  "path": "/collect/lowest"
                                                },
                                                "title": {
                                                  "dict_translator": null,
                                                  "id": "name"
                                                }
                                              }
                                            }
                                          }
                                        ]
                                      }
                                    }
                                  ]
                                }
                              }
                            ]
                          }
                        }
                      ]
                    }
                  }
                ]
              }
            }

        self.writeDict(card_menu_dict)
        return card_menu_dict

    def get_card_menu(self):
        user_data = session.get('logged_in_user', None)
        if user_data:
            user_id = user_data['user_id']
            username = user_data['username']
        else:
            user_id = -1

#        print("user_id: {0}".format(user_id))

        return {'result': True, 'data': self.card_menu_dict['default'], 'error': None}

def getCardMenuInstance():
    cm = CardMenu.getInstance()
#    card_menu = {}
#    config["path"] = cb.getConfigPath()

    return cm
