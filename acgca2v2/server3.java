
import java.security.*;
import java.security.cert.CertificateException;
import java.security.cert.CertificateFactory;
import java.security.cert.X509Certificate;
import java.security.spec.PKCS8EncodedKeySpec;
import java.net.*;
import java.awt.RenderingHints.Key;
import java.io.*;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.file.*;
import javax.crypto.*;
import javax.crypto.spec.*;
import java.security.*;
import sun.misc.*;
import java.util.*;
import java.text.*;

public class server3 {

	@SuppressWarnings("deprecation")
	public static void main (String [] args ) throws IOException, Exception, CertificateException, NoSuchProviderException, SignatureException,InvalidKeyException{
	    ServerSocket serverSocket = new ServerSocket(15123);
            Socket ssocket = null;
            
            while(true){
                //get connection
                ssocket = getConnection(serverSocket ,ssocket);
                
                if(ssocket != null){
                    try{
                        while(true) {

                            //Download option
                            byte[] opbytes = new byte[16348];
                            ssocket.getInputStream().read(opbytes);
                            String option = new String(opbytes);

                            //Non secure method
                            if (option.contains("no")) {
                                URL myimage = new URL("https://lh3.googleusercontent.com/-Q7RCF7aLY0g/AAAAAAAAAAI/AAAAAAAAABQ/1N8737kZ59g/s640-il/photo.jpg");
                                DataOutputStream dos = new DataOutputStream(ssocket.getOutputStream());
                                DataInputStream in = null;
                                try{ in = new DataInputStream(myimage.openStream()); }
                                catch (Exception ee)
                                { 
                                    System.out.println(ee);
                                    System.out.println("Check internet connection please");
                                  ssocket.close(); return;
                                }
                                try
                                { while (true) { dos.writeByte(in.readByte()); } }
                                catch (EOFException ee)
                                  { System.out.println("-------------- Done ----------"); in.close();}

                                dos.flush();
                                dos.close();
                                    ssocket.close();
                                    System.exit(0);
                            }
                            //End of non secure method
                            else {

                                //get image
                                URL myimage = new URL("https://lh3.googleusercontent.com/-Q7RCF7aLY0g/AAAAAAAAAAI/AAAAAAAAABQ/1N8737kZ59g/s640-il/photo.jpg");
                                DataInputStream in = null;
                                try{ 
                                        in = new DataInputStream(myimage.openStream()); }
                                catch (Exception ee)
                                { 
                                        System.out.println(ee);
                                        System.out.println("Check internet connection please");
                                        ssocket.close(); return;
                                }

                                ByteArrayOutputStream buffer = new ByteArrayOutputStream();
                                byte[] bytes = new byte[16384];
                                int x = 0;
                                while((x = in.read(bytes, 0, bytes.length))!= -1){
                                    buffer.write(bytes, 0, x);
                                }
                                buffer.flush();
                                byte[] imagebytes = buffer.toByteArray();

                                //Certificate
                                CertificateFactory cert = CertificateFactory.getInstance("X.509");
                                FileInputStream info = new FileInputStream("server.cert");
                                java.security.cert.Certificate printCert = cert.generateCertificate(info);
                                info.close();
                                PublicKey pubKey = printCert.getPublicKey();
                                System.out.println("\nGetting private key...");
                                PrivateKey priKey = getPrivateKey("private_key.der");
                                try{
                                    printCert.verify(pubKey);
                                }catch(NoSuchAlgorithmException | InvalidKeyException | NoSuchProviderException | SignatureException e){
                                    System.out.println(e);
                                }
                                X509Certificate servCert = (X509Certificate) printCert;

                                //Sending the certificate over
                                ByteBuffer bbc = ByteBuffer.allocate(4);
                                bbc.putInt(servCert.getEncoded().length);       
                                OutputStream abc = ssocket.getOutputStream();
                                try{
                                    System.out.println("Sending cert");
                                    abc.write(bbc.array());
                                    abc.write(servCert.getEncoded());
                                } catch (Exception ee){
                                    System.out.println(ee);
                                } 
                                abc.flush();
                                System.out.println("-------------- Done Sending Cert -------------\n");

                                //Get AES Key from client and decrypt it
                                System.out.println("Receiving the AES key...");
                                byte[] lenb = new byte[4];
                                ssocket.getInputStream().read(lenb,0,4);
                                ByteBuffer bb = ByteBuffer.wrap(lenb);
                                int len = bb.getInt();
                                byte[] getaeskey = new byte[len];
                                ssocket.getInputStream().read(getaeskey);
                                System.out.println("Key received\n");
                                Cipher cipher = Cipher.getInstance("RSA/ECB/PKCS1Padding");
                                cipher.init(Cipher.DECRYPT_MODE, priKey);
                                byte[] decryptedaes = cipher.doFinal(getaeskey);
                                SecretKeySpec aeskey = new SecretKeySpec(decryptedaes, "AES");

                                //Encrypt data with key
                                System.out.println("Encrypting the image...");
                                Cipher cipher2 = Cipher.getInstance("AES/ECB/PKCS5Padding");
                                cipher2.init(Cipher.ENCRYPT_MODE, aeskey);
                                byte[] encryptedimg = cipher2.doFinal(imagebytes);
                                System.out.println("Encrypted\n");

                                //Create signature
                                System.out.println("Generating signature and hash...\n");
                                Signature signature = Signature.getInstance("SHA256withRSA");
                                signature.initSign(priKey);
                                MessageDigest digest = MessageDigest.getInstance("SHA-256");
                                byte[] hash = digest.digest(encryptedimg);
                                signature.update(hash);
                                byte[] realSig = signature.sign();

                                //Send encrypted image and signature + hash to client
                                System.out.println("Sending the encrypted image and signature+hash over\n");
                                ByteBuffer bb2 = ByteBuffer.allocate(4);
                                bb2.putInt(encryptedimg.length);
                                abc.write(bb2.array());
                                abc.write(encryptedimg);

                                ByteBuffer bb3 = ByteBuffer.allocate(4);
                                bb3.putInt(realSig.length);
                                abc.write(bb3.array());
                                abc.write(realSig);

                                ssocket.close();
                                System.out.println("Done!");
                                //System.exit(0);
                                //System.out.println("Listening for new connection..");
                            }
                        }
                    }catch(SocketException e){
                        System.out.println("Connection closed!");
                    }
                } else {
                    System.out.println("Error getting connection.");
                    System.out.println("Listening for new connection...\n");
                }
            }
            //System.out.println("Server closing! bye c:");
}
	public static String asHex (byte buf[]) {

		  //Obtain a StringBuffer object
		      StringBuffer strbuf = new StringBuffer(buf.length * 2);
		      int i;

		      for (i = 0; i < buf.length; i++) {
		          if (((int) buf[i] & 0xff) < 0x10)
		             strbuf.append("0");
		             strbuf.append(Long.toString((int) buf[i] & 0xff, 16));
		       }
		       // Return result string in Hexadecimal format
		       return strbuf.toString();
		  }
	public static PrivateKey getPrivateKey(String filename) throws Exception {

        byte[] keyBytes = Files.readAllBytes(Paths.get(filename));

        PKCS8EncodedKeySpec spec = new PKCS8EncodedKeySpec(keyBytes);
        KeyFactory kf = KeyFactory.getInstance("RSA");
        return kf.generatePrivate(spec);
        }
        
        public static Socket getConnection(ServerSocket serverSocket, Socket ssocket){
            try{
                System.out.println("Listening for connection...");
                ssocket = serverSocket.accept();
                System.out.println("Connection successful\n");
                return ssocket;
            } catch(IOException e){
                System.out.println("Connection error, try again!\n");
                return ssocket;
            }
        }
}
