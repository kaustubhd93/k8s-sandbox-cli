output "instance_public_ip" {
  value = aws_instance.dev_node.public_ip
}
output "instance_private_ip" {
  value = aws_instance.dev_node.private_ip
}