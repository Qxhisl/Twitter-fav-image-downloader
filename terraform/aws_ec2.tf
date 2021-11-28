# EC2インスタンスの作成
resource "aws_instance" "server" {
  ami                    = "ami-036d0684fc96830ca" # Ubuntu Server 20.04 LTS(HVM), SSD Volume Type
  instance_type          = "t2.micro"
  subnet_id              = aws_subnet.subnet.id
  vpc_security_group_ids = [aws_security_group.sg.id]
  key_name               = aws_key_pair.key.id
  user_data              = file("cloud-config.cfg")
  tags = {
    "Name" = "Twitter-fav-image-downloader"
  }
}

resource "aws_key_pair" "key" {
  key_name   = "key"
  public_key = file("~/.ssh/id_rsa.pub")
}