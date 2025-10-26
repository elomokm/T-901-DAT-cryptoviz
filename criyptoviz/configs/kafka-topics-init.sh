topics-init:
  image: confluentinc/cp-kafka:7.6.1
  container_name: cv_topics_init
  depends_on:
    kafka:
      condition: service_healthy
  entrypoint: ["/bin/bash","/opt/topics-init.sh"]
  volumes:
    - ./configs/kafka-topics-init.sh:/opt/topics-init.sh:ro
  networks:
    - cryptoviz_net