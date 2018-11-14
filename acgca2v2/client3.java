
import java.security.*;
import java.security.cert.CertificateFactory;
import java.security.cert.X509Certificate;
import java.security.spec.X509EncodedKeySpec;
import java.net.*; 
import java.io.*;
import java.nio.ByteBuffer;
import java.nio.file.*;
import javax.crypto.*;
import javax.crypto.spec.*;
import java.util.concurrent.TimeUnit;
import java.awt.Color;
import java.awt.Container;
import java.awt.Font;
import java.awt.HeadlessException;
import java.awt.event.ActionListener;
import javax.swing.*;
import javax.swing.Timer;

import java.security.*;
import sun.misc.*;
import java.util.*;
import java.text.*;

public class client3 extends JWindow{

	static boolean isRegistered;
    private static JProgressBar progressBar = new JProgressBar();
    private static client3 execute;
    private static int count;
    private static Timer timer1;
    
	public static void main(String [] args) throws IOException, Exception {
	    
		String fname = "image.jpg";
		
	    //Connect
		Socket csocket = new Socket("127.0.0.1",15123);
		
		//FTP option
		int n = JOptionPane.showConfirmDialog(
			    null,
			    "This is the Institue of Higher Learning Technology FTP server.\nWould you like download the file securely?",
			    "IHL Tech FTP Server",
			    JOptionPane.YES_NO_OPTION);
		String option = null;
		if (n == 0) {
			option = "yes";
		}
		//Non secure
		else if (n == 1) {
			option = "no";
			byte[] opbytes = option.getBytes();
			csocket.getOutputStream().write(opbytes);
			DataInputStream in = null;
		    try{ in = new DataInputStream(csocket.getInputStream()); }
		    catch (Exception ee)
		    { System.out.println("Check connection please");
		      csocket.close(); return;
		    }
		    FileOutputStream fos = new FileOutputStream(fname);

		    try
		    {while (true)
		       fos.write(in.readByte());
		    }
		    catch (EOFException ee)
		    {  System.out.println("File transfer complete");
		       in.close();
		    }
		    fos.flush();
		    fos.close();
		    csocket.close();
		    JOptionPane.showMessageDialog(null, "File transfer complete", "FTP",JOptionPane.PLAIN_MESSAGE);
		    System.exit(0);
		} else {
                    System.exit(0);
                }
		//End of non secure method
		
		byte[] opbytes = option.getBytes();
		csocket.getOutputStream().write(opbytes);
        
		// get cert
		System.out.println("Connected to server\nGetting certificate from server...");
	    byte[] certBytes = null;
	    String cert;
	    InputStream stream = csocket.getInputStream();
	    try{
	            byte[] lenb = new byte[4];
	            stream.read(lenb,0,4);
	            ByteBuffer bb = ByteBuffer.wrap(lenb);
	            int len = bb.getInt();

	            byte[] mkb = new byte[len];
	            stream.read(mkb);
	            certBytes = mkb;
	            cert = asHex(mkb);   
	    }
	    catch (Exception ee){
	       System.out.println(ee);
	    }
	    //construct cert from server
	    CertificateFactory certFactory = CertificateFactory.getInstance("X.509");
	    InputStream certStream = new ByteArrayInputStream(certBytes);
	    X509Certificate servCert = (X509Certificate)certFactory.generateCertificate(certStream);
	    
	    //get public key from cert
	    PublicKey pubKey = servCert.getPublicKey();
	    
	    //verify cert 
	    System.out.println("\nVerifying certificate...");
	    //if theres no exception caught then theres no error
	    try{
	        servCert.verify(pubKey);
	        System.out.println("Certificate verified\n");
	    }catch(NoSuchAlgorithmException | InvalidKeyException | NoSuchProviderException | SignatureException e){
	        System.out.println(e);
	    }
	    
	  //Generate AES
        System.out.println("Generating a symmetric (AES) key...");
        KeyGenerator keyGenerator = KeyGenerator.getInstance("AES");
        keyGenerator.init(128);
        Key AESKey = keyGenerator.generateKey();
        System.out.println("AES key generated");
		
        //AES Encryption & sending
        Cipher cipher = Cipher.getInstance("RSA/ECB/PKCS1Padding");
        cipher.init(Cipher.ENCRYPT_MODE, pubKey);
        byte[] aesbytes = AESKey.getEncoded();
        byte[] cipheraes = cipher.doFinal(aesbytes);
        try{
            System.out.println("Sending the encrypted AES key...");
    	    ByteBuffer bb2 = ByteBuffer.allocate(4);
            bb2.putInt(cipheraes.length);
            csocket.getOutputStream().write(bb2.array());
            csocket.getOutputStream().write(cipheraes);
            System.out.println("Key successfully sent\n");
            }catch (Exception e) {
            	System.out.println(e);
            }
        
        //Get the encrypted image + hash and sig
        byte[] lenb = new byte[4];
        csocket.getInputStream().read(lenb,0,4);
        ByteBuffer bb = ByteBuffer.wrap(lenb);
        int len = bb.getInt();
        byte[] getencimg = new byte[len];
        csocket.getInputStream().read(getencimg);
        
        byte[] lenb2 = new byte[4];
        csocket.getInputStream().read(lenb2,0,4);
        ByteBuffer bb2 = ByteBuffer.wrap(lenb2);
        int len2 = bb2.getInt();
        byte[] gethashsig = new byte[len2];
        csocket.getInputStream().read(gethashsig);
        
        //Checking the hash and verifying before decrypting
        System.out.println("Verifying signature...");
    	MessageDigest digest = MessageDigest.getInstance("SHA-256");
        byte[] hash = digest.digest(getencimg);
    	Signature sig = Signature.getInstance("SHA256withRSA");
    	sig.initVerify(pubKey);
    	sig.update(hash);
    	//The checking stuff
    	try {
    	if(sig.verify(gethashsig)) {
    		System.out.println("Signature verified\n");
    		JOptionPane.showMessageDialog(null, "Signature verified. Click OK to download the image", "IHL FTP Server",JOptionPane.PLAIN_MESSAGE);
    		Cipher cipher2 = Cipher.getInstance("AES/ECB/PKCS5Padding");
	        cipher2.init(Cipher.DECRYPT_MODE, AESKey);
	        byte[] decryptedimg = cipher2.doFinal(getencimg);
	        //Create the image
		    FileOutputStream fos = new FileOutputStream(fname);
		    fos.write(decryptedimg);
		    execute = new client3();
		    System.out.println("Writing the image...\n");
		    TimeUnit.SECONDS.sleep(4);
		    JOptionPane.showMessageDialog(null, "Image has been downloaded.", "IHL FTP Server",JOptionPane.PLAIN_MESSAGE);
		    fos.flush();
		    fos.close();
		    csocket.close();
		    System.out.println("Done");
		    System.exit(0);		
    	}else {
    		JOptionPane.showMessageDialog(null, "Signature incorrect. The image will not be downloaded.", "IHL FTP Server",JOptionPane.PLAIN_MESSAGE);
    		csocket.getInputStream().close();
		    csocket.getOutputStream().close();
    		csocket.close();
    		System.exit(0);
    	}
    	}catch (Exception e) {
    		System.out.println(e);
    		System.exit(0);
    	}
    	
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
	public client3() {

        Container container = getContentPane();
        container.setLayout(null);

        JPanel panel = new JPanel();
        panel.setBorder(new javax.swing.border.EtchedBorder());
        panel.setBackground(new Color(255, 255, 255));
        panel.setBounds(10, 10, 348, 150);
        panel.setLayout(null);
        container.add(panel);

        JLabel label = new JLabel("Downloading image...");
        label.setFont(new Font("Verdana", Font.BOLD, 14));
        label.setBounds(85, 25, 280, 30);
        panel.add(label);

        progressBar.setMaximum(50);
        progressBar.setBounds(55, 180, 250, 15);
        container.add(progressBar);
        loadProgressBar();
        setSize(370, 215);
        setLocationRelativeTo(null);
        setVisible(true);
    }
	private void loadProgressBar() {
        ActionListener al = new ActionListener() {

            public void actionPerformed(java.awt.event.ActionEvent evt) {
                count++;

                progressBar.setValue(count);

                if (count == 50) {

                    execute.setVisible(false);//swapped this around with timer1.stop()

                    timer1.stop();
                }

            }

        };
        timer1 = new Timer(50, al);
        timer1.start();
    }
}
