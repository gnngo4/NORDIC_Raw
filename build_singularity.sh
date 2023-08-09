docker build -t nordic .
docker tag nordic localhost:5000/nordic
docker push localhost:5000/nordic
rm nordic.simg
SINGULARITY_NOHTTPS=1 singularity build nordic.simg docker://localhost:5000/nordic
