const { PrismaClient } = require('@prisma/client');

async function checkDiscordMetrics() {
  const prisma = new PrismaClient({
    datasources: {
      db: {
        url: 'postgres://neondb_owner:npg_VKJPW8pIfQq0@ep-calm-butterfly-a55pupnn-pooler.us-east-2.aws.neon.tech/neondb?connect_timeout=15&sslmode=require'
      }
    }
  });

  try {
    console.log('🔗 PostgreSQL接続開始...');
    
    // discord_metricsテーブルのデータ確認
    const discordMetrics = await prisma.discord_metrics.findMany({
      orderBy: { createdAt: 'desc' },
      take: 10
    });
    
    console.log(`📊 discord_metricsテーブル: ${discordMetrics.length}件のレコード`);
    
    if (discordMetrics.length > 0) {
      console.log('📅 最新のデータ:');
      discordMetrics.forEach(metric => {
        console.log(`  ${metric.date.toISOString().split('T')[0]}: メンバー${metric.memberCount}人, メッセージ${metric.dailyMessages}件`);
        console.log(`    ID: ${metric.id}, 作成日時: ${metric.createdAt}`);
      });
      
      // 今日のデータがあるかチェック
      const today = new Date().toISOString().split('T')[0];
      const todayData = discordMetrics.find(m => m.date.toISOString().split('T')[0] === today);
      console.log(`📅 今日(${today})のデータ: ${todayData ? '存在' : '存在しない'}`);
    } else {
      console.log('❌ discord_metricsテーブルにデータが存在しません');
    }
    
    // テーブル構造の確認
    console.log('\n📋 テーブル構造の詳細確認...');
    
    // 手動でスキーマ情報を取得
    const tableInfo = await prisma.$queryRaw`
      SELECT column_name, data_type, is_nullable, column_default
      FROM information_schema.columns 
      WHERE table_name = 'discord_metrics'
      ORDER BY ordinal_position
    `;
    
    console.log('📋 discord_metricsのカラム:');
    tableInfo.forEach(col => {
      console.log(`  - ${col.column_name}: ${col.data_type} (NULL: ${col.is_nullable}, DEFAULT: ${col.column_default || 'なし'})`);
    });
    
  } catch (error) {
    console.error('❌ エラー:', error.message);
    console.error('詳細:', error);
  } finally {
    await prisma.$disconnect();
  }
}

checkDiscordMetrics();